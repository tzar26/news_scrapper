from __future__ import annotations

import asyncio

from news_scraper.agents.graph import run_agent
from news_scraper.db.session import SessionLocal


async def main() -> None:
    """Прогоняет 2 вопроса через агента, печатает ответы."""
    questions = [
        'Что происходит с ключевой ставкой ЦБ?',
        'Сравни ситуацию с нефтью и газом в России',
    ]
    async with SessionLocal() as session:
        for q in questions:
            print(f'\n=== {q} ===')
            result = await run_agent(session, q)
            print(f'Iterations: {result["iterations"]}')
            print(f'Answer: {result["answer"]}')


if __name__ == '__main__':
    asyncio.run(main())
