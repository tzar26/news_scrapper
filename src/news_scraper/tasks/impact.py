"""Celery-задачи для оценки влияния на рынок (Market Impact)."""

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
from news_scraper.nlp.market_impact import extract_market_impact
from news_scraper.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

LOCK_KEY = 'lock:impact_batch'
LOCK_TTL_SECONDS = 600


class LLMUnavailableError(Exception):
    """Вызывается, когда Ollama недоступна."""


@dataclass
class ImpactResult:
    processed: int
    remaining: int
    deadline_hit: bool


async def _impact_batch(batch_size: int, deadline_seconds: float) -> ImpactResult:
    """Оценивает влияние на рынок для партии статей."""
    start = time.monotonic()
    deadline = start + deadline_seconds
    processed = 0
    deadline_hit = False

    async with SessionLocal() as session:
        repo = ArticleRepository(session)
        items = await repo.get_without_market_impact(limit=batch_size)
        if not items:
            return ImpactResult(processed=0, remaining=0, deadline_hit=False)

        for item in items:
            if time.monotonic() >= deadline:
                deadline_hit = True
                logger.warning('deadline reached, stopping at %d processed', processed)
                break

            try:
                impact = await extract_market_impact(item.title, item.text)
            except (httpx.ConnectError, httpx.ReadTimeout, ollama.ResponseError) as exc:
                logger.warning('LLM unavailable during impact extraction: %s', exc)
                raise LLMUnavailableError('Ollama is not reachable') from exc

            # Сохраняем, даже если словарь пустой (чтобы не зацикливаться)
            await repo.set_market_impact(item.id, impact)
            processed += 1
            logger.info(
                'impact article id=%d: %s (%d/%d)',
                item.id,
                impact.get('importance', 'unknown'),
                processed,
                len(items),
            )

    async with SessionLocal() as session:
        repo = ArticleRepository(session)
        remaining_items = await repo.get_without_market_impact(limit=1)
        remaining = 1 if remaining_items else 0

    return ImpactResult(processed=processed, remaining=remaining, deadline_hit=deadline_hit)


async def _run_impact_and_dispose(batch_size: int, deadline_seconds: float) -> ImpactResult:
    """Обёртка: запускает оценку и освобождает пул соединений."""
    try:
        return await _impact_batch(batch_size, deadline_seconds)
    finally:
        await engine.dispose()


@celery_app.task(name='news_scraper.tasks.impact.impact_batch')
def impact_batch(batch_size: int = 50, deadline_seconds: float = 480.0) -> dict:
    """Celery-обёртка: оценка Market Impact с распределённой блокировкой."""
    if not acquire_lock(LOCK_KEY, ttl_seconds=LOCK_TTL_SECONDS):
        logger.info('impact_batch skipped: lock held')
        return {'status': 'skipped', 'reason': 'already_running'}

    try:
        result = asyncio.run(_run_impact_and_dispose(batch_size, deadline_seconds))
        logger.info(
            'impact_batch done: processed=%d deadline_hit=%s', result.processed, result.deadline_hit
        )
        return {
            'status': 'ok',
            'processed': result.processed,
            'deadline_hit': result.deadline_hit,
        }
    except LLMUnavailableError:
        logger.warning('impact_batch skipped: LLM unavailable')
        return {'status': 'skipped', 'reason': 'llm_unavailable'}
    finally:
        release_lock(LOCK_KEY)
