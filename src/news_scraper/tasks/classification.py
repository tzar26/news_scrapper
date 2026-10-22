"""Celery-задачи для классификации статей (LLM)."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

import httpx
import ollama

from news_scraper.db.repositories import ArticleRepository
from news_scraper.db.session import SessionLocal, engine
from news_scraper.infra.redis_client import acquire_lock, release_lock
from news_scraper.nlp.classifier import classify_article
from news_scraper.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

LOCK_KEY = 'lock:classify_batch'
LOCK_TTL_SECONDS = 600


class LLMUnavailableError(Exception):
    """Вызывается, когда Ollama недоступна."""


@dataclass
class ClassificationResult:
    processed: int
    remaining: int
    deadline_hit: bool


async def _classify_batch(batch_size: int, deadline_seconds: float) -> ClassificationResult:
    """Классифицирует партию статей без предсказанной категории."""
    start = time.monotonic()
    deadline = start + deadline_seconds
    processed = 0
    deadline_hit = False

    async with SessionLocal() as session:
        repo = ArticleRepository(session)
        items = await repo.get_without_category(limit=batch_size)
        if not items:
            return ClassificationResult(processed=0, remaining=0, deadline_hit=False)

        for item in items:
            if time.monotonic() >= deadline:
                deadline_hit = True
                logger.warning('deadline reached, stopping at %d processed', processed)
                break

            try:
                category = await classify_article(item.title, item.text)
            except (httpx.ConnectError, httpx.ReadTimeout, ollama.ResponseError) as exc:
                logger.warning('LLM unavailable during classification: %s', exc)
                raise LLMUnavailableError('Ollama is not reachable') from exc

            await repo.set_predicted_category(item.id, category.value)
            processed += 1
            logger.info(
                'classified article id=%d as %s (%d/%d)',
                item.id,
                category.value,
                processed,
                len(items),
            )

    async with SessionLocal() as session:
        repo = ArticleRepository(session)
        remaining_items = await repo.get_without_category(limit=1)
        remaining = 1 if remaining_items else 0

    return ClassificationResult(processed=processed, remaining=remaining, deadline_hit=deadline_hit)


async def _run_classify_and_dispose(
    batch_size: int, deadline_seconds: float
) -> ClassificationResult:
    """Обёртка: запускает классификацию и освобождает пул соединений.

    Нужна, чтобы Celery (который создаёт новый event loop на каждый вызов
    asyncio.run) получал свежие соединения из пула.
    """
    try:
        return await _classify_batch(batch_size, deadline_seconds)
    finally:
        await engine.dispose()


@celery_app.task(name='news_scraper.tasks.classification.classify_batch')
def classify_batch(batch_size: int = 50, deadline_seconds: float = 480.0) -> dict:
    """Celery-обёртка: классифицирует статьи с распределённой блокировкой."""
    if not acquire_lock(LOCK_KEY, ttl_seconds=LOCK_TTL_SECONDS):
        logger.info('classify_batch skipped: lock held')
        return {'status': 'skipped', 'reason': 'already_running'}

    try:
        result = asyncio.run(_run_classify_and_dispose(batch_size, deadline_seconds))
        logger.info(
            'classify_batch done: processed=%d deadline_hit=%s',
            result.processed,
            result.deadline_hit,
        )
        return {
            'status': 'ok',
            'processed': result.processed,
            'deadline_hit': result.deadline_hit,
        }
    except LLMUnavailableError:
        logger.warning('classify_batch skipped: LLM unavailable')
        return {'status': 'skipped', 'reason': 'llm_unavailable'}
    finally:
        release_lock(LOCK_KEY)
