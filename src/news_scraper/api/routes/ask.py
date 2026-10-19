from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.api.deps import get_db_session
from news_scraper.api.schemas import AskRequest, AskResponse, SourceRefResponse
from news_scraper.rag.chains import answer_question

router = APIRouter(prefix='/ask', tags=['rag'])


@router.post('', response_model=AskResponse)
async def ask(
    request: AskRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AskResponse:
    """Отвечает на вопрос, опираясь на статьи из БД.
    Возвращает текст ответа с цитатами вида [article_N] и список
    источников, на которые сослалась модель.
    """
    result = await answer_question(
        session,
        request.question,
        top_k=request.top_k,
        rerank=request.rerank,
    )
    sources = [SourceRefResponse(id=s.id, url=s.url, title=s.title) for s in result.sources]
    return AskResponse(answer=result.answer, sources=sources)
