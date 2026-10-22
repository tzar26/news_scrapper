"""Прямой вызов run_agent_stream без FastAPI и Streamlit."""

from __future__ import annotations

import asyncio
import logging

from news_scraper.agents.graph import run_agent_stream
from news_scraper.db.session import SessionLocal

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s [%(name)s] %(message)s')


async def main() -> None:
    """Читает генератор стрима и печатает каждый чанк."""
    async with SessionLocal() as session:
        question = 'Сколько статей про энергетику мы собрали за последние 3 дня?'
        print(f'--- ВОПРОС: {question} ---')

        try:
            async for chunk in run_agent_stream(session, question):
                print(f'CHUNK: {chunk!r}')
        except Exception:
            print('\n!!! ИСКЛЮЧЕНИЕ В ГЕНЕРАТОРЕ !!!')
            import traceback

            traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
