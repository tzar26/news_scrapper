"""Retriever с hybrid search: BM25 + vector + RRF."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.db.models import Article
from news_scraper.domain.enums import Category, Country
from news_scraper.infra.ollama_client import OllamaClient

RRF_K = 60
_QUERY_MULTIPLIER = 6
_CYRILLIC_RE = re.compile('[а-яА-Я]')


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
    rrf_score: float
    content_hash: str
    related: list[RelatedArticle] = field(default_factory=list)


def _detect_lang(query: str) -> str:
    """Определяет язык запроса для полнотекстового поиска.

    Простая эвристика: если есть кириллица — 'russian', иначе 'english'.
    """
    return 'russian' if _CYRILLIC_RE.search(query) else 'english'


async def _search_vector(
    session: AsyncSession,
    query: str,
    *,
    top_n: int,
    country: Country | None,
    category: Category | None,
    client: OllamaClient,
    days_ago: int | None = None,
) -> list[tuple[Article, float]]:
    """Векторный поиск. Возвращает [(Article, distance), ...] по distance ASC."""
    vec = await client.embed(query)
    distance_expr = Article.embedding.cosine_distance(vec).label('distance')
    stmt = (
        select(Article, distance_expr)
        .where(Article.embedding.is_not(None))
        .order_by(distance_expr)
        .limit(top_n)
    )
    if country is not None:
        stmt = stmt.where(Article.country == country.value)
    if category is not None:
        stmt = stmt.where(Article.category == category.value)
    if days_ago is not None:
        cutoff = datetime.now(UTC) - timedelta(days=days_ago)
        stmt = stmt.where(Article.published_at >= cutoff)
    result = await session.execute(stmt)
    return [(row[0], float(row[1])) for row in result.all()]


async def _search_bm25(
    session: AsyncSession,
    query: str,
    *,
    top_n: int,
    country: Country | None,
    category: Category | None,
    days_ago: int | None = None,
) -> list[tuple[Article, float]]:
    """BM25-поиск через PostgreSQL tsvector. Возвращает [(Article, rank), ...]."""
    lang = _detect_lang(query)

    where_extra = ''
    params: dict[str, object] = {'q': query, 'lim': top_n}
    if country is not None:
        where_extra += ' AND country = :country'
        params['country'] = country.value
    if category is not None:
        where_extra += ' AND category = :category'
        params['category'] = category.value
    if days_ago is not None:
        where_extra += ' AND published_at >= :cutoff'
        params['cutoff'] = datetime.now(UTC) - timedelta(days=days_ago)

    sql = text(
        f"""
        SELECT id,
               ts_rank_cd(
                   to_tsvector('{lang}', title || ' ' || text),
                   plainto_tsquery('{lang}', :q)
               ) AS rank
        FROM articles
        WHERE to_tsvector('{lang}', title || ' ' || text)
              @@ plainto_tsquery('{lang}', :q)
        {where_extra}
        ORDER BY rank DESC
        LIMIT :lim
        """
    )

    result = await session.execute(sql, params)
    rows = result.all()
    if not rows:
        return []

    ids = [row.id for row in rows]
    rank_map = {row.id: float(row.rank) for row in rows}

    articles_stmt = select(Article).where(Article.id.in_(ids))
    articles_result = await session.execute(articles_stmt)
    articles_map = {a.id: a for a in articles_result.scalars().all()}

    return [(articles_map[row.id], rank_map[row.id]) for row in rows if row.id in articles_map]


def _rrf_fuse(
    vector_results: list[tuple[Article, float]],
    bm25_results: list[tuple[Article, float]],
    *,
    k: int = RRF_K,
) -> list[tuple[Article, float]]:
    """Объединяет результаты двух методов через Reciprocal Rank Fusion.

    RRF_score(d) = sum(1 / (k + rank_i(d))).
    Возвращает [(Article, rrf_score), ...] по score DESC.
    """
    scores: dict[int, float] = {}
    articles: dict[int, Article] = {}

    for rank, (article, _) in enumerate(vector_results, start=1):
        scores[article.id] = scores.get(article.id, 0.0) + 1.0 / (k + rank)
        articles[article.id] = article

    for rank, (article, _) in enumerate(bm25_results, start=1):
        scores[article.id] = scores.get(article.id, 0.0) + 1.0 / (k + rank)
        articles[article.id] = article

    ordered_ids = sorted(scores, key=lambda aid: scores[aid], reverse=True)
    return [(articles[aid], scores[aid]) for aid in ordered_ids]


async def search(
    session: AsyncSession,
    query: str,
    *,
    top_k: int = 5,
    country: Country | None = None,
    category: Category | None = None,
    client: OllamaClient | None = None,
    days_ago: int | None = None,
) -> list[SearchResult]:
    """Hybrid-поиск: BM25 + vector + RRF + дедупликация по content_hash.

    Args:
        session: сессия БД.
        query: текстовый запрос.
        top_k: сколько уникальных историй вернуть.
        country: фильтр по стране.
        category: фильтр по категории.
        client: OllamaClient; если None — создаётся и закрывается внутри.

    Returns:
        Список SearchResult, отсортированный по RRF-релевантности.
        Пустой список при пустом query или отсутствии результатов.
    """
    if not query.strip():
        return []

    owns_client = client is None
    if client is None:
        client = OllamaClient()

    try:
        top_n = top_k * _QUERY_MULTIPLIER

        vector_results = await _search_vector(
            session,
            query,
            top_n=top_n,
            country=country,
            category=category,
            client=client,
            days_ago=days_ago,
        )
        bm25_results = await _search_bm25(
            session,
            query,
            top_n=top_n,
            country=country,
            category=category,
            days_ago=days_ago,
        )

        fused = _rrf_fuse(vector_results, bm25_results)

        groups: dict[str, SearchResult] = {}
        for article, score in fused:
            if article.content_hash not in groups:
                groups[article.content_hash] = SearchResult(
                    representative_id=article.id,
                    representative_url=article.url,
                    title=article.title,
                    text=article.text,
                    rrf_score=score,
                    content_hash=article.content_hash,
                )
            else:
                groups[article.content_hash].related.append(
                    RelatedArticle(
                        id=article.id,
                        url=article.url,
                        source=article.source,
                    )
                )

        return list(groups.values())[:top_k]

    finally:
        if owns_client:
            await client.aclose()


async def search_with_rerank(
    session: AsyncSession,
    query: str,
    *,
    top_k: int = 5,
    candidates: int = 30,
    country: Country | None = None,
    category: Category | None = None,
    client: OllamaClient | None = None,
    reranker: Any | None = None,
    days_ago: int | None = None,
) -> list[SearchResult]:
    """Hybrid search + cross-encoder reranking.

    Схема: hybrid search (vector + BM25 + RRF) → top-N кандидатов →
    cross-encoder rerank → top_k.

    Args:
        session: сессия БД.
        query: текстовый запрос.
        top_k: сколько результатов вернуть после reranking.
        candidates: сколько кандидатов взять из hybrid search.
        country: фильтр по стране.
        category: фильтр по категории.
        client: OllamaClient; если None — создаётся внутри.
        reranker: Reranker; если None — создаётся дефолтный.

    Returns:
        Список SearchResult, отсортированный по reranking-оценке.
    """
    results = await search(
        session,
        query,
        top_k=candidates,
        country=country,
        category=category,
        client=client,
        days_ago=days_ago,
    )
    if not results:
        return []
    if reranker is None:
        from news_scraper.rag.reranker import Reranker

        reranker = Reranker()
    return reranker.rerank(query, results, top_k=top_k)
