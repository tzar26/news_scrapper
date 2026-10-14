"""Debug: показывает, что именно уходит в LLM."""

from __future__ import annotations

import asyncio

from news_scraper.db.session import SessionLocal
from news_scraper.rag.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, format_context
from news_scraper.rag.retriever import search


async def main() -> None:
    """Формирует промпт, печатает его целиком."""
    async with SessionLocal() as session:
        question = 'Что нового с ключевой ставкой ЦБ?'
        results = await search(session, question, top_k=3)
        context = format_context(results)

        print(f'=== SYSTEM PROMPT ({len(SYSTEM_PROMPT)} chars) ===')
        print(SYSTEM_PROMPT)
        print()

        user_prompt = USER_PROMPT_TEMPLATE.format(question=question, context=context)
        print(f'=== USER PROMPT ({len(user_prompt)} chars) ===')
        print(user_prompt)


if __name__ == '__main__':
    asyncio.run(main())
