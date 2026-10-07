from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from news_scraper.infra.settings import settings

# Module-level variables
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Function
async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a DB session and closes it after the request."""
    async with SessionLocal() as session:
        yield session
