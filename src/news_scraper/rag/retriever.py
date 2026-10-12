from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.db.models import Article
from news_scraper.domain.enums import Category, Country
from news_scraper.infra.ollama_client import OllamaClient


@dataclass
class RelatedArticle:
    """Перепечатка статьи (другой источник, тот же content_hash)."""

    id: int
    url: str
    source: str


@dataclass
class SearchResult:
    """Результат поиска: одна уникальная история + её перепечатки."""

    representative_id: int
    representative_url: str
    title: str
    text: str
    distance: float
    content_hash: str
    related: list[RelatedArticle] = field(default_factory=list)


async def search(
    session: AsyncSession,
    query: str,
    *,
    top_k: int = 5,
    country: Country | None = None,
    category: Category | None = None,
    client: OllamaClient | None = None,
) -> list[SearchResult]:
    """Ищет top_k уникальных историй, релевантных запросу.
    Дедуплицирует по content_hash: одна история = одна запись в ответе,
    перепечатки складываются в related.
    Args:
        session: сессия БД.
        query: текстовый запрос на естественном языке.
        top_k: сколько уникальных историй вернуть.
        country: фильтр по стране (опционально).
        category: фильтр по категории (опционально).
        client: OllamaClient; если None — создаётся и закрывается внутри.
    Returns:
        Список SearchResult, отсортированный по distance ASC.
        Пустой список, если ничего не найдено или query пуст.
    """
    if query.strip() == '':
        return []

    owns_client = client is None
    if client is None:
        client = OllamaClient()

    try:
        vec = await client.embed(query)
        distance_expr = Article.embedding.cosine_distance(vec).label('distance')
        stmt = (
            select(Article, distance_expr)
            .where(Article.embedding.is_not(None))
            .order_by(distance_expr)
            .limit(top_k * 3)  # с запасом под дедупликацию
        )
        if country is not None:
            stmt = stmt.where(Article.country == country.value)
        if category is not None:
            stmt = stmt.where(Article.category == category.value)
        result = await session.execute(stmt)
        rows = result.all()  # список Row(Article, distance)
        # Дедупликация:
        groups: dict[str, SearchResult] = {}
        for article, distance in rows:
            if article.content_hash not in groups:
                groups[article.content_hash] = SearchResult(
                    representative_id=article.id,
                    representative_url=article.url,
                    title=article.title,
                    text=article.text,
                    distance=float(distance),
                    content_hash=article.content_hash,
                )
            else:
                groups[article.content_hash].related.append(
                    RelatedArticle(id=article.id, url=article.url, source=article.source)
                )

        results = sorted(groups.values(), key=lambda r: r.distance)[:top_k]
        return results

    finally:
        if owns_client:
            await client.aclose()
