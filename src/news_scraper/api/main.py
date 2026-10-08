"""FastAPI-приложение проекта."""

from __future__ import annotations

from fastapi import FastAPI

from news_scraper.api.routes.articles import router as articles_router
from news_scraper.api.routes.stats import router as stats_router

app = FastAPI(
    title='News Scraper API',
    version='0.1.0',
    description='API для доступа к собранным новостям',
)

app.include_router(articles_router)
app.include_router(stats_router)


@app.get('/health', tags=['system'])
async def health() -> dict[str, str]:
    """Проверка работоспособности сервиса."""
    return {'status': 'ok'}
