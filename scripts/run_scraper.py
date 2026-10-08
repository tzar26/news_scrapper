from __future__ import annotations

import asyncio

from news_scraper.db.repositories import ArticleRepository
from news_scraper.db.session import SessionLocal
from news_scraper.scraper.sources.registry import ALL_SOURCES


async def main() -> None:
    """
    Проходит по всем источникам, сохраняет в БД, печатает статистику.
    """
    total_fetched = 0
    total_inserted = 0
    async with SessionLocal() as session:
        repo = ArticleRepository(session)
        for source_cls in ALL_SOURCES:
            source = source_cls()
            try:
                items = await source.fetch()
            except Exception as e:
                print(f'[{source.name}] ERROR: {e}')
                continue
            finally:
                await source.aclose()
            inserted = await repo.insert_many(items)
            total_fetched += len(items)
            total_inserted += inserted
            print(f'[{source.name}] fetched={len(items)}, inserted={inserted}')
    print(f'TOTAL: fetched={total_fetched}, inserted={total_inserted}')


if __name__ == '__main__':
    asyncio.run(main())
