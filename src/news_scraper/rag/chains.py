from __future__ import annotations

import re
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.infra.ollama_client import OllamaClient
from news_scraper.infra.settings import settings
from news_scraper.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, format_context
from news_scraper.rag.retriever import SearchResult, search

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

    Ищет паттерн ``[article_N]``, сопоставляет N с id из results
    (включая related-перепечатки), возвращает в порядке появления
    в тексте, без дублей.

    Args:
        answer_text: текст ответа LLM.
        results: результаты retrieval, отданные в контекст.

    Returns:
        Список SourceRef в порядке первого упоминания в ответе.
        Если id в тексте нет в results — пропускается (галлюцинация).
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
    model: str = DEFAULT_MODEL,
    client: OllamaClient | None = None,
) -> RAGAnswer:
    """Отвечает на вопрос, опираясь на статьи из БД.
    Пайплайн: retrieval → промпт → ChatOllama → парсинг цитирований.
    Args:
    session: сессия БД.
    question: вопрос пользователя.
    top_k: сколько уникальных историй подать в контекст.
    model: имя модели в Ollama.
    client: OllamaClient; если None — создаётся и закрывается внутри.
    Returns:
    RAGAnswer с ответом, источниками и сырыми results.
    Если ничего не найдено — answer='В базе нет информации
    по этому запросу.', sources=[].
    """
    owns_client = client is None
    if client is None:
        client = OllamaClient()
    try:
        results = await search(session, question, top_k=top_k, client=client)
        if not results:
            return RAGAnswer(
                answer='В базе нет информации по этому запросу.',
                sources=[],
                results=[],
            )
        context = format_context(results)
        user_prompt = USER_PROMPT_TEMPLATE.format(question=question, context=context)
        llm = ChatOllama(
            model=model,
            temperature=0.1,
            num_ctx=16384,
            base_url=settings.ollama_base_url,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = await llm.ainvoke(messages)
        answer_text = response.content  # type: ignore[union-attr]
        sources = _extract_sources(answer_text, results)
        return RAGAnswer(answer=answer_text, sources=sources, results=results)
    finally:
        if owns_client:
            await client.aclose()
