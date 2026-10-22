"""Прямой запуск агента для отладки get_metrics."""

from __future__ import annotations

import asyncio
import logging

from news_scraper.agents.graph import run_agent
from news_scraper.db.session import SessionLocal

# Включаем логирование, чтобы видеть вызовы инструментов
logging.basicConfig(level=logging.INFO, format='%(levelname)s [%(name)s] %(message)s')


async def main() -> None:
    """Прогоняет вопрос с метриками напрямую."""
    async with SessionLocal() as session:
        question = 'Сколько статей про энергетику мы собрали за последние 3 дня?'
        print(f'--- ВОПРОС: {question} ---')

        try:
            result = await run_agent(session, question)
            print(f'\n--- ОТВЕТ ---\n{result["answer"]}')
            print(f'\nШагов сделано: {result["iterations"]}')
        except Exception:
            print('\n!!! ПОЙМАНО ИСКЛЮЧЕНИЕ !!!')
            import traceback

            traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
