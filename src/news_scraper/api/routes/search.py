from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.api.deps import get_db_session
from news_scraper.api.schemas import (
    RelatedArticleResponse,
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
)
from news_scraper.rag.retriever import search

router = APIRouter(prefix='/search', tags=['search'])


@router.post('', response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    """
    Семантический поиск по статьям (hybrid: BM25 + vector + RRF).
    Возвращает top_k уникальных историй без вызова LLM.
    Быстрее /ask, потому что нет генерации.
    """
    results = await search(session, request.query, top_k=request.top_k)
    return SearchResponse(
        query=request.query,
        results=[
            SearchResultResponse(
                representative_id=r.representative_id,
                url=r.representative_url,
                title=r.title,
                text=r.text[:500],
                rrf_score=r.rrf_score,
                related=[
                    RelatedArticleResponse(id=rel.id, url=rel.url, source=rel.source)
                    for rel in r.related
                ],
            )
            for r in results
        ],
    )
