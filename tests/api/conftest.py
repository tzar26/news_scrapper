"""Pytest fixtures для API-тестов с использованием Testcontainers."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from news_scraper.api.deps import get_db_session
from news_scraper.api.main import app
from news_scraper.db import models  # noqa: F401 — регистрирует модели в metadata
from news_scraper.db.base import Base


@pytest.fixture(scope='session')
def postgres_container():
    """Поднимает одноразовый контейнер PostgreSQL для всех тестов сессии."""
    # Используем тот же образ, что и в docker-compose (pgvector)
    with PostgresContainer('pgvector/pgvector:pg17') as postgres:
        yield postgres


@pytest_asyncio.fixture(scope='session')
async def test_engine(postgres_container):
    """Создаёт async engine, подключённый к тестовому контейнеру.

    Применяет миграции Alembic для создания схемы (включая pgvector).
    """
    # Получаем URL, но заменяем драйвер на asyncpg (testcontainers по умолчанию даёт psycopg2)
    raw_url = postgres_container.get_connection_url()
    # postgresql+psycopg2://... -> postgresql+asyncpg://...
    async_url = raw_url.replace('postgresql+psycopg2', 'postgresql+asyncpg').replace(
        'postgresql://', 'postgresql+asyncpg://'
    )

    # Создаём engine
    engine = create_async_engine(async_url, echo=False)

    # ВАЖНО: Включаем расширение vector, так как Alembic может не сделать это в тестовой базе
    async with engine.begin() as conn:
        await conn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS vector;')
        # Создаём все таблицы из метаданных (быстрее, чем прогонять все миграции)
        # Если хочешь тестировать именно миграции, можно вызвать alembic upgrade head,
        # но для API-тестов достаточно create_all.
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    """Даёт чистую сессию БД для каждого теста (с откатом после)."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        # Откатываем всё, что тест успел записать (хотя API-тесты у нас read-only)
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session) -> AsyncIterator[AsyncClient]:
    """AsyncClient, работающий с FastAPI app, но с тестовой БД."""

    # Переопределяем зависимость get_db_session, чтобы FastAPI использовал нашу тестовую сессию
    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c

    # Убираем override после теста
    app.dependency_overrides.clear()
