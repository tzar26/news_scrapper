from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.db.models import Article
from news_scraper.domain.dedup import content_hash
from news_scraper.domain.models import RawNewsItem


class ArticleRepository:
    """
    Repository for managing articles in the database.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_many(self, items: list[RawNewsItem]) -> int:
        """
        Inserts articles, skipping duplicates by URL or content_hash.
        Returns the number of actually inserted records.
        """
        if not items:
            return 0

        rows = [
            {
                'url': str(item.url),
                'content_hash': content_hash(item),
                'title': item.title,
                'source': item.source,
                'country': item.country.value,
                'category': item.category.value,
                'published_at': item.published_at,
                'text': item.text,
                'summary': item.summary,
            }
            for item in items
        ]

        stmt = pg_insert(Article).values(rows).on_conflict_do_nothing()
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount or 0
