from news_scraper.api.schemas.agent import AgentRequest, AgentResponse
from news_scraper.api.schemas.article import (
    ArticleDetailResponse,
    ArticleResponse,
    ArticlesPage,
)
from news_scraper.api.schemas.ask import AskRequest, AskResponse, SourceRefResponse
from news_scraper.api.schemas.search import (
    RelatedArticleResponse,
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
)
from news_scraper.api.schemas.stats import CountItem, StatsResponse

__all__ = [
    'CountItem',
    'StatsResponse',
    'ArticleDetailResponse',
    'ArticleResponse',
    'ArticlesPage',
    'AskRequest',
    'AskResponse',
    'SourceRefResponse',
    'RelatedArticleResponse',
    'SearchRequest',
    'SearchResponse',
    'SearchResultResponse',
    'AgentRequest',
    'AgentResponse',
]
"""
Pydantic-схемы API.
"""
