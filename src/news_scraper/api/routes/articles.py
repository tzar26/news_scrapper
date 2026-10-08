from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from news_scraper.api.deps import get_article_repo
from news_scraper.api.schemas import (
    ArticleDetailResponse,
    ArticleResponse,
    ArticlesPage,
)
from news_scraper.db.repositories import ArticleRepository
from news_scraper.domain.enums import Country

router = APIRouter(prefix='/articles', tags=['articles'])


@router.get('', response_model=ArticlesPage)
async def list_articles(
    country: Country | None = Query(default=None, description='Фильтр по стране'),
    source: str | None = Query(default=None, description='Фильтр по источнику'),
    category: str | None = Query(default=None, description='Фильтр по категории'),
    limit: int = Query(default=50, ge=1, le=200, description='Размер страницы'),
    offset: int = Query(default=0, ge=0, description='Смещение'),
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticlesPage:
    """Возвращает список статей с фильтрами и пагинацией."""
    articles = await repo.list_with_filters(
        country=country,
        source=source,
        category=category,
        limit=limit,
        offset=offset,
    )
    total = await repo.count_with_filters(
        country=country,
        source=source,
        category=category,
    )
    return ArticlesPage(
        items=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get('/{article_id}', response_model=ArticleDetailResponse)
async def get_article(
    article_id: int,
    repo: ArticleRepository = Depends(get_article_repo),
) -> ArticleDetailResponse:
    """Возвращает детальную информацию о статье по id."""
    article = await repo.get_by_id(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail='Article not found')
    return ArticleDetailResponse.model_validate(article)
