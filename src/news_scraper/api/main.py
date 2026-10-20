"""FastAPI-приложение проекта."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import ollama
from fastapi import FastAPI

from news_scraper.api.routes.agent import router as agent_router
from news_scraper.api.routes.articles import router as articles_router
from news_scraper.api.routes.ask import router as ask_router
from news_scraper.api.routes.search import router as search_router
from news_scraper.api.routes.stats import router as stats_router
from news_scraper.infra.ollama_client import OllamaClient
from news_scraper.infra.redis_client import _redis_client
from news_scraper.infra.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)

logger = logging.getLogger(__name__)


async def _warmup_models() -> None:
    """Прогревает обе модели Ollama при старте приложения.

    Загружает bge-m3 (embeddings) и qwen2.5-coder (chat) в VRAM,
    чтобы первый пользовательский запрос не ждал ~20 секунд.
    Ошибки логируются, но не валят приложение — если Ollama
    недоступен, стартуем, но медленно.
    """
    chat_model = 'qwen2.5-coder:14b-16k'
    try:
        client = OllamaClient()
        try:
            await client.embed('warmup')
            logger.info('warmup: bge-m3 loaded')
        finally:
            await client.aclose()

        ollama_client = ollama.AsyncClient(host=settings.ollama_base_url)
        await ollama_client.chat(
            model=chat_model,
            messages=[{'role': 'user', 'content': 'hi'}],
            options={'num_ctx': 4096},
            stream=False,
        )
        logger.info('warmup: %s loaded', chat_model)
    except Exception as exc:
        logger.warning('warmup failed (Ollama unavailable?): %s', exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управляет жизненным циклом приложения: прогрев при старте."""
    logger.info('starting up: warming up Ollama models...')
    await _warmup_models()
    yield
    logger.info('shutting down')


app = FastAPI(
    title='News Scraper API',
    version='0.1.0',
    description='API для доступа к собранным новостям',
    lifespan=lifespan,
)

app.include_router(articles_router)
app.include_router(stats_router)
app.include_router(ask_router)
app.include_router(search_router)
app.include_router(agent_router)


@app.get('/health', tags=['system'])
async def health() -> dict[str, str]:
    """Проверка работоспособности сервиса."""
    return {'status': 'ok'}


@app.get('/health/source_errors', tags=['system'])
async def source_errors() -> list[dict]:
    """Возвращает список ошибок парсинга источников из Redis."""
    errors_json = _redis_client.get('scraper:last_errors')
    if not errors_json:
        return []
    try:
        return json.loads(errors_json)
    except Exception:
        return []


if __name__ == '__main__':
    """Запуск для отладки."""
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)
