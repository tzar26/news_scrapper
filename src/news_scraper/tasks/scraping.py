"""Задачи Celery для сбора новостей."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

from news_scraper.db.repositories import ArticleRepository
from news_scraper.db.session import SessionLocal
from news_scraper.infra.redis_client import _redis_client
from news_scraper.scraper.sources.registry import ALL_SOURCES
from news_scraper.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

ERRORS_KEY = 'scraper:last_errors'


@dataclass
class ScrapingResult:
    fetched: int
    inserted: int
    failed_sources: list[dict]


async def run_scraping() -> ScrapingResult:
    """Проходит по всем источникам и сохраняет новые статьи."""
    total_fetched = 0
    total_inserted = 0
    failed = []

    async with SessionLocal() as session:
        repo = ArticleRepository(session)
        for source_cls in ALL_SOURCES:
            source = source_cls()
            try:
                items = await source.fetch()
            except Exception as exc:
                logger.exception('source %s failed', source.name)
                failed.append(
                    {
                        'source': source.name,
                        'error': str(exc),
                    }
                )
                continue
            finally:
                await source.aclose()

            inserted = await repo.insert_many(items)
            total_fetched += len(items)
            total_inserted += inserted
            logger.info(
                'source=%s fetched=%d inserted=%d',
                source.name,
                len(items),
                inserted,
            )

    # Сохраняем ошибки в Redis для отображения в UI
    if failed:
        _redis_client.set(ERRORS_KEY, json.dumps(failed, ensure_ascii=False))
    else:
        _redis_client.delete(ERRORS_KEY)

    return ScrapingResult(
        fetched=total_fetched,
        inserted=total_inserted,
        failed_sources=failed,
    )


@celery_app.task(name='news_scraper.tasks.scraping.scrape_all_sources')
def scrape_all_sources() -> dict:
    """Celery-обёртка: синхронно запускает асинхронный run_scraping."""
    result = asyncio.run(run_scraping())
    logger.info(
        'scraping done: fetched=%d inserted=%d failed=%d',
        result.fetched,
        result.inserted,
        len(result.failed_sources),
    )
    return {
        'fetched': result.fetched,
        'inserted': result.inserted,
        'failed_sources': result.failed_sources,
    }
