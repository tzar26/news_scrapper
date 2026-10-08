from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from news_scraper.api.main import app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """
    AsyncClient, работающий с FastAPI app без реального сервера.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        yield c
