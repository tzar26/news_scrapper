from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.db.models import Article
from news_scraper.domain.dedup import content_hash
from news_scraper.domain.models import Country, RawNewsItem


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

    async def get_by_id(self, article_id: int) -> Article | None:
        """
        Возвращает статью по id или None.
        """
        result = await self._session.execute(select(Article).where(Article.id == article_id))
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        country: Country | None = None,
        source: str | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Article]:
        """
        Возвращает статьи с фильтрами и пагинацией.
        Сортировка — по published_at DESC, id DESC.
        """
        stmt = select(Article).order_by(Article.published_at.desc(), Article.id.desc())
        if country is not None:
            stmt = stmt.where(Article.country == country.value)
        if source is not None:
            stmt = stmt.where(Article.source == source)
        if category is not None:
            stmt = stmt.where(Article.category == category)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_with_filters(
        self,
        *,
        country: Country | None = None,
        source: str | None = None,
        category: str | None = None,
    ) -> int:
        """
        Возвращает общее число статей, подходящих под фильтры.
        Использовать func.count() из sqlalchemy.
        Возвращает int.
        """
        stmt = select(func.count()).select_from(Article)
        if country is not None:
            stmt = stmt.where(Article.country == country.value)
        if source is not None:
            stmt = stmt.where(Article.source == source)
        if category is not None:
            stmt = stmt.where(Article.category == category)
        result = await self._session.execute(stmt)
        return result.scalar_one()
