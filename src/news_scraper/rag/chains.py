"""RAG chain: retrieval + LLM через прямой ollama SDK.

LangChain не используется — на нашем объёме его оверхед (streaming
агрегация, обёртки) даёт 9x замедление без функциональных преимуществ.
Для LangGraph-агента LangChain остаётся в agents/.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import ollama
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.infra.ollama_client import OllamaClient
from news_scraper.infra.settings import settings
from news_scraper.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, format_context
from news_scraper.rag.retriever import SearchResult, search, search_with_rerank

DEFAULT_MODEL = 'qwen2.5-coder:14b-16k'
CITATION_PATTERN = re.compile(r'\[article_(\d+)\]')


@dataclass
class SourceRef:
    """Источник, упомянутый в ответе LLM."""

    id: int
    url: str
    title: str


@dataclass
class RAGAnswer:
    """Ответ RAG-пайплайна."""

    answer: str
    sources: list[SourceRef] = field(default_factory=list)
    results: list[SearchResult] = field(default_factory=list)


def _extract_sources(
    answer_text: str,
    results: list[SearchResult],
) -> list[SourceRef]:
    """Извлекает уникальные источники, упомянутые в ответе.

    Ищет [article_N], сопоставляет с id из results (включая related),
    возвращает в порядке появления в тексте, без дублей.
    """
    seen_ids = dict.fromkeys(int(match) for match in CITATION_PATTERN.findall(answer_text))

    source_map: dict[int, tuple[str, str]] = {}
    for result in results:
        source_map[result.representative_id] = (
            result.representative_url,
            result.title,
        )
        for related in result.related:
            source_map[related.id] = (related.url, result.title)

    return [
        SourceRef(
            id=article_id,
            url=source_map[article_id][0],
            title=source_map[article_id][1],
        )
        for article_id in seen_ids
        if article_id in source_map
    ]


async def answer_question(
    session: AsyncSession,
    question: str,
    *,
    top_k: int = 5,
    rerank: bool = False,
    model: str = DEFAULT_MODEL,
    client: OllamaClient | None = None,
) -> RAGAnswer:
    """Отвечает на вопрос, опираясь на статьи из БД.

    Пайплайн: retrieval (hybrid) → промпт → ollama.chat → парсинг цитат.

    Args:
        session: сессия БД.
        question: вопрос пользователя.
        top_k: сколько уникальных историй подать в контекст.
        rerank: если True — применить cross-encoder reranking
        (jina-reranker-v2). Улучшает top-1, но замедляет ответ
        на 1-2 сек. По умолчанию False.
        model: имя модели в Ollama.
        client: OllamaClient для embed; если None — создаётся внутри.

    Returns:
        RAGAnswer. Если retrieval пустой — answer с сообщением,
        sources=[].
    """
    owns_client = client is None
    if client is None:
        client = OllamaClient()

    try:
        if rerank:
            results = await search_with_rerank(
                session,
                question,
                top_k=top_k,
                candidates=30,
                client=client,
            )
        else:
            results = await search(session, question, top_k=top_k, client=client)
        if not results:
            return RAGAnswer(
                answer='В базе нет информации по этому запросу.',
                sources=[],
                results=[],
            )

        context = format_context(results)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            context=context,
        )

        ollama_client = ollama.AsyncClient(host=settings.ollama_base_url)
        response = await ollama_client.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            options={
                'num_ctx': 4096,
                'temperature': 0.3,
            },
            stream=False,
        )

        answer_text = response['message']['content']
        sources = _extract_sources(answer_text, results)
        return RAGAnswer(answer=answer_text, sources=sources, results=results)

    finally:
        if owns_client:
            await client.aclose()
