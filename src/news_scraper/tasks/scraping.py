from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from news_scraper.db.repositories import ArticleRepository
from news_scraper.db.session import SessionLocal
from news_scraper.scraper.sources.registry import ALL_SOURCES
from news_scraper.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@dataclass
class ScrapingResult:
    fetched: int
    inserted: int
    failed_sources: list[str]


async def run_scraping() -> ScrapingResult:
    """Проходит по всем источникам из реестра и сохраняет новые статьи.
    Ошибки отдельных источников не прерывают общий процесс —
    имя источника попадает в failed_sources.
    """
    total_fetched = 0
    total_inserted = 0
    failed = []

    async with SessionLocal() as session:
        repo = ArticleRepository(session)
        for source_cls in ALL_SOURCES:
            source = source_cls()
            try:
                items = await source.fetch()
            except Exception:
                logger.exception('source %s failed', source.name)
                failed.append(source.name)
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
        'scraping done: fetched=%d inserted=%d failed=%s',
        result.fetched,
        result.inserted,
        result.failed_sources,
    )
    return {
        'fetched': result.fetched,
        'inserted': result.inserted,
        'failed_sources': result.failed_sources,
    }
