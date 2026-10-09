# задача: NER/sentiment/embeddings

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from news_scraper.db.repositories import ArticleRepository
from news_scraper.db.session import SessionLocal, engine
from news_scraper.infra.ollama_client import OllamaClient
from news_scraper.infra.redis_client import acquire_lock, release_lock
from news_scraper.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

LOCK_KEY = 'lock:enrich_batch'
LOCK_TTL_SECONDS = 600


@dataclass
class EnrichmentResult:
    processed: int
    remaining: int
    deadline_hit: bool
    skipped_reason: str | None = None


async def _enrich_batch(batch_size: int, deadline_seconds: float) -> EnrichmentResult:
    """Считает эмбеддинги для партии статей без embedding.
    Останавливается раньше при приближении к deadline_seconds (мягкий останов).
    Обрабатывает статьи последовательно.
    """
    start = time.monotonic()
    deadline = start + deadline_seconds
    client = OllamaClient()
    processed = 0
    deadline_hit = False
    try:
        async with SessionLocal() as session:
            repo = ArticleRepository(session)
            items = await repo.get_without_embedding(limit=batch_size)
            if not items:
                return EnrichmentResult(processed=0, remaining=0, deadline_hit=False)
            for item in items:
                if time.monotonic() >= deadline:
                    deadline_hit = True
                    logger.warning('deadline reached, stopping at %d processed', processed)
                    break
                text = f'{item.title}\n\n{item.text}'.strip()
                vector = await client.embed(text)
                await repo.set_embedding(item.id, vector)
                processed += 1
                logger.info('embedded article id=%d (%d/%d)', item.id, processed, len(items))
            # remaining — сколько ещё без эмбеддинга
            async with SessionLocal() as session:
                repo = ArticleRepository(session)
                remaining_items = await repo.get_without_embedding(limit=1)
                remaining = 1 if remaining_items else 0
            return EnrichmentResult(
                processed=processed, remaining=remaining, deadline_hit=deadline_hit
            )
    finally:
        await client.aclose()
        await engine.dispose()


@celery_app.task(name='news_scraper.tasks.enrichment.enrich_batch')
def enrich_batch(batch_size: int = 50, deadline_seconds: float = 480.0) -> dict:
    """Celery-обёртка: enrich_batch с распределённой блокировкой.
    deadline_seconds = 480 (8 минут) — мягкий лимит до жёсткого 600.
    Если блокировка занята — задача скипается (не ждёт).
    """
    if not acquire_lock(LOCK_KEY, ttl_seconds=LOCK_TTL_SECONDS):
        logger.info('enrich_batch skipped: lock held')
        return {'status': 'skipped', 'reason': 'already_running'}
    try:
        result = asyncio.run(_enrich_batch(batch_size, deadline_seconds))
        logger.info(
            'enrich_batch done: processed=%d deadline_hit=%s', result.processed, result.deadline_hit
        )
        return {
            'status': 'ok',
            'processed': result.processed,
            'deadline_hit': result.deadline_hit,
        }
    finally:
        release_lock(LOCK_KEY)
