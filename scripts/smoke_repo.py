"""Smoke-тест репозитория: fetch Kommersant → insert → повтор → 0 новых."""

from __future__ import annotations

import asyncio

from news_scraper.db.repositories import ArticleRepository
from news_scraper.db.session import SessionLocal
from news_scraper.scraper.sources.kommersant import KommersantSource


async def run_once(label: str) -> int:
    """Fetch + insert, печатает результат."""
    source = KommersantSource()
    try:
        items = await source.fetch()
    finally:
        await source.aclose()

    async with SessionLocal() as session:
        repo = ArticleRepository(session)
        inserted = await repo.insert_many(items)

    print(f'[{label}] fetched={len(items)}, inserted={inserted}')
    return inserted


async def main() -> None:
    """Прогоняет два раза и проверяет, что второй раз вставок 0."""
    first = await run_once('1st')
    second = await run_once('2nd')

    if first > 0 and second == 0:
        print('OK: dedup работает')
    else:
        print(f'FAIL: ожидалось first>0, second=0; получили {first}, {second}')


if __name__ == '__main__':
    asyncio.run(main())
