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

    async def stats(self) -> dict:
        """
        Возвращает агрегированную статистику по статьям.
        Ключи: total, by_country, by_source, by_category,
        latest_published_at, earliest_published_at.
        by_country/by_source/by_category — списки dict вида
        {'country'|'source'|'category': str, 'count': int}, сортировка
        по count DESC.
        """
        total = await self._session.scalar(select(func.count()).select_from(Article))

        country_rows = await self._session.execute(
            select(Article.country, func.count().label('count'))
            .group_by(Article.country)
            .order_by(func.count().desc())
        )
        by_country = [{'country': row.country, 'count': row.count} for row in country_rows]

        source_rows = await self._session.execute(
            select(Article.source, func.count().label('count'))
            .group_by(Article.source)
            .order_by(func.count().desc())
        )
        by_source = [{'source': row.source, 'count': row.count} for row in source_rows]

        category_rows = await self._session.execute(
            select(Article.category, func.count().label('count'))
            .group_by(Article.category)
            .order_by(func.count().desc())
        )
        by_category = [{'category': row.category, 'count': row.count} for row in category_rows]

        date_row = await self._session.execute(
            select(
                func.min(Article.published_at).label('earliest'),
                func.max(Article.published_at).label('latest'),
            )
        )
        dates = date_row.one()

        return {
            'total': total or 0,
            'by_country': by_country,
            'by_source': by_source,
            'by_category': by_category,
            'latest_published_at': dates.latest,
            'earliest_published_at': dates.earliest,
        }

    async def get_without_embedding(self, limit: int = 50) -> list[Article]:
        """
        Возвращает статьи без эмбеддинга (embedding IS NULL).
        Сортировка по id DESC (новые первыми), лимит.
        """
        stmt = (
            select(Article)
            .where(Article.embedding.is_(None))
            .order_by(Article.id.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def set_embedding(self, article_id: int, embedding: list[float]) -> None:
        """
        Сохраняет эмбеддинг для статьи и коммитит.
        """
        article = await self._session.get(Article, article_id)
        if article:
            article.embedding = embedding
            await self._session.commit()
