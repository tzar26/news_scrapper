from __future__ import annotations

from fastapi import APIRouter, Depends

from news_scraper.api.deps import get_article_repo
from news_scraper.api.schemas import CountItem, StatsResponse
from news_scraper.db.repositories import ArticleRepository

router = APIRouter(prefix='/stats', tags=['stats'])


@router.get('', response_model=StatsResponse)
async def get_stats(
    repo: ArticleRepository = Depends(get_article_repo),
) -> StatsResponse:
    """Возвращает агрегированную статистику по всем статьям."""
    data = await repo.stats()
    by_country = [CountItem(key=row['country'], count=row['count']) for row in data['by_country']]
    by_source = [CountItem(key=row['source'], count=row['count']) for row in data['by_source']]
    by_category = [
        CountItem(key=row['category'], count=row['count']) for row in data['by_category']
    ]
    return StatsResponse(
        total_articles=data['total'],
        by_country=by_country,
        by_source=by_source,
        by_category=by_category,
        latest_published_at=data['latest_published_at'],
        earliest_published_at=data['earliest_published_at'],
    )
