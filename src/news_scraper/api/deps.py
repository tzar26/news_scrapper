from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.db.repositories import ArticleRepository
from news_scraper.db.session import SessionLocal


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: сессия БД, автоматически закрывается после запроса."""
    async with SessionLocal() as session:
        yield session


def get_article_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ArticleRepository:
    """FastAPI dependency: репозиторий статей с уже открытой сессией."""
    return ArticleRepository(session)
