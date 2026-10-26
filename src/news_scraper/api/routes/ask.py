from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.api.deps import get_db_session
from news_scraper.api.schemas import AskRequest, AskResponse, SourceRefResponse
from news_scraper.rag.chains import answer_question, answer_question_stream

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
        days_ago=request.days_ago,
        use_hyde=request.use_hyde,
    )
    sources = [SourceRefResponse(id=s.id, url=s.url, title=s.title) for s in result.sources]
    return AskResponse(answer=result.answer, sources=sources)


@router.post('/stream')
async def ask_stream(
    request: AskRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Стриминговый RAG-ответ (Server-Sent Events).

    Возвращает text/event-stream. Каждое событие — кусок текста.
    В конце приходит событие с префиксом '__SOURCES__' и JSON-ом источников.
    """

    async def event_generator():
        async for chunk in answer_question_stream(
            session,
            request.question,
            top_k=request.top_k,
            rerank=request.rerank,
            days_ago=request.days_ago,
            use_hyde=request.use_hyde,
        ):
            # В SSE нельзя передавать переносы строк (они интерпретируются как конец события)
            # Поэтому экранируем их как \\n
            safe_chunk = chunk.replace('\n', '\\n')
            yield f'data: {safe_chunk}\n\n'

    return StreamingResponse(event_generator(), media_type='text/event-stream')
