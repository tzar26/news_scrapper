from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


@pytest.mark.asyncio
async def test_list_articles_returns_page(client: AsyncClient):
    response = await client.get('/articles?limit=5')
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'total' in data
    assert 'limit' in data
    assert 'offset' in data
    assert len(data['items']) <= 5
    assert data['total'] >= 0


@pytest.mark.asyncio
async def test_list_articles_filter_by_country(client: AsyncClient):
    response = await client.get('/articles?country=russia&limit=3')
    assert response.status_code == 200
    data = response.json()
    assert all(item['country'] == 'russia' for item in data['items'])


@pytest.mark.asyncio
async def test_list_articles_invalid_country(client: AsyncClient):
    response = await client.get('/articles?country=atlantis')
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_article_not_found(client: AsyncClient):
    response = await client.get('/articles/999999999')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stats_returns_expected_shape(client: AsyncClient):
    response = await client.get('/stats')
    assert response.status_code == 200
    data = response.json()
    assert 'total_articles' in data
    assert 'by_country' in data
    assert 'by_source' in data
    assert 'by_category' in data
    assert 'latest_published_at' in data
    assert 'earliest_published_at' in data
    assert isinstance(data['by_country'], list)
    assert isinstance(data['by_source'], list)
    assert isinstance(data['by_category'], list)
    assert all('key' in item and 'count' in item for item in data['by_country'])
    assert all('key' in item and 'count' in item for item in data['by_source'])
    assert all('key' in item and 'count' in item for item in data['by_category'])


@pytest.mark.asyncio
async def test_stats_filters_not_supported(client: AsyncClient):
    response = await client.get('/stats?country=russia')
    assert response.status_code == 200
