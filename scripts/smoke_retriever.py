from __future__ import annotations

import asyncio

from news_scraper.db.session import SessionLocal
from news_scraper.rag.retriever import search

QUERIES = [
    'ключевая ставка ЦБ',
    'нефть добыча ОПЕК',
    'автомобильный рынок Китая',
]


async def main() -> None:
    """Прогоняет запросы, печатает топ-5 историй и число перепечаток."""
    async with SessionLocal() as session:
        for query in QUERIES:
            print(f'\n=== {query} ===')
            results = await search(session, query, top_k=5)
            for i, r in enumerate(results, 1):
                extra = f' (+{len(r.related)} related)' if r.related else ''
                print(f'{i}. [{r.distance:.3f}] {r.title[:70]}{extra}')


if __name__ == '__main__':
    asyncio.run(main())
