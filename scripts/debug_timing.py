"""Точный замер: сколько времени занимает каждая часть RAG-пайплайна."""

from __future__ import annotations

import asyncio
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from news_scraper.db.session import SessionLocal
from news_scraper.infra.ollama_client import OllamaClient
from news_scraper.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, format_context
from news_scraper.rag.retriever import search


async def main() -> None:
    """Замер по этапам: embed → search → prompt → LLM."""
    async with SessionLocal() as session:
        client = OllamaClient()
        try:
            # 1. Embed запроса
            t0 = time.monotonic()
            vec = await client.embed('Что нового с ключевой ставкой ЦБ?')
            t_embed = time.monotonic() - t0
            print(f'1. embed запроса:  {t_embed:.2f}s (dim={len(vec)})')

            # 2. Search (vector + BM25 + RRF)
            t0 = time.monotonic()
            results = await search(
                session,
                'Что нового с ключевой ставкой ЦБ?',
                top_k=3,
                client=client,
            )
            t_search = time.monotonic() - t0
            print(f'2. search:         {t_search:.2f}s ({len(results)} результатов)')

            # 3. Формирование промпта
            t0 = time.monotonic()
            context = format_context(results)
            user_prompt = USER_PROMPT_TEMPLATE.format(
                question='Что нового с ключевой ставкой ЦБ?',
                context=context,
            )
            t_prompt = time.monotonic() - t0
            total_chars = len(SYSTEM_PROMPT) + len(user_prompt)
            print(f'3. промпт:         {t_prompt:.2f}s ({total_chars} символов)')

            # 4. LLM через LangChain
            llm = ChatOllama(
                model='qwen2.5-coder:14b-16k',
                temperature=0.1,
                num_ctx=4096,
                base_url='http://192.168.0.118:11434',
            )
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]
            t0 = time.monotonic()
            response = await llm.ainvoke(messages)
            t_llm = time.monotonic() - t0
            print(f'4. LLM:            {t_llm:.2f}s')
            print(f'   ответ ({len(response.content)} символов): {response.content[:200]}')

            print(f'\n--- TOTAL: {t_embed + t_search + t_prompt + t_llm:.2f}s ---')
        finally:
            await client.aclose()


if __name__ == '__main__':
    asyncio.run(main())
