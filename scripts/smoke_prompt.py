"""Smoke-тест форматирования контекста для RAG-промпта."""

from __future__ import annotations

import asyncio

from news_scraper.db.session import SessionLocal
from news_scraper.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, format_context
from news_scraper.rag.retriever import search


async def main() -> None:
    """Форматирует контекст для одного запроса и печатает первые 800 знаков."""
    async with SessionLocal() as session:
        results = await search(session, 'нефть ОПЕК', top_k=3)
        context = format_context(results)
        prompt = USER_PROMPT_TEMPLATE.format(
            question='Что происходит с нефтью?',
            context=context,
        )
        print('--- SYSTEM ---')
        print(SYSTEM_PROMPT[:200], '...')
        print('\n--- USER (первые 800) ---')
        print(prompt[:800])


if __name__ == '__main__':
    asyncio.run(main())
