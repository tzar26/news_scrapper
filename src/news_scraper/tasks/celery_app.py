from __future__ import annotations

from celery import Celery

from news_scraper.infra.settings import settings

celery_app = Celery(
    'news_scraper',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['news_scraper.tasks.scraping', 'news_scraper.tasks.enrichment'],
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        'scrape-all-sources-hourly': {
            'task': 'news_scraper.tasks.scraping.scrape_all_sources',
            'schedule': 3600.0,
        },
        'enrich-batch-every-5-min': {
            'task': 'news_scraper.tasks.enrichment.enrich_batch',
            'schedule': 300.0,
        },
    },
)
