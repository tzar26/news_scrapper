from news_scraper.api.schemas.article import (
    ArticleDetailResponse,
    ArticleResponse,
    ArticlesPage,
)
from news_scraper.api.schemas.ask import AskRequest, AskResponse, SourceRefResponse
from news_scraper.api.schemas.stats import CountItem, StatsResponse

__all__ = [
    'ArticleDetailResponse',
    'ArticleResponse',
    'ArticlesPage',
    'AskRequest',
    'AskResponse',
    'SourceRefResponse',
]
"""
Pydantic-схемы API.
"""
