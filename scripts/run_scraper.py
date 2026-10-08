from __future__ import annotations

import asyncio

from news_scraper.tasks.scraping import run_scraping


async def main() -> None:
    """
    Запускает сбор всех источников и печатает статистику.
    """
    result = await run_scraping()
    print(f'TOTAL: fetched={result.fetched}, inserted={result.inserted}')
    if result.failed_sources:
        print(f'FAILED: {result.failed_sources}')


if __name__ == '__main__':
    asyncio.run(main())
