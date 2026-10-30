from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.agents.graph import run_agent, run_agent_stream
from news_scraper.api.deps import get_db_session
from news_scraper.api.schemas import AgentRequest, AgentResponse

router = APIRouter(prefix='/agent', tags=['agent'])


@router.post('', response_model=AgentResponse)
async def agent_endpoint(
    request: AgentRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AgentResponse:
    """Отвечает на вопрос через LangGraph-агента.
    Агент сам решает, какие инструменты вызвать (поиск по статьям),
    выполняет multi-step рассуждения и формирует ответ.
    Может быть медленнее /ask из-за нескольких шагов.
    """
    result = await run_agent(session, request.question, history=request.history)
    return AgentResponse(
        answer=result['answer'],
        iterations=result['iterations'],
    )


@router.post('/stream')
async def agent_stream_endpoint(
    request: AgentRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Стриминговый запуск агента (SSE)."""

    async def event_generator():
        async for chunk in run_agent_stream(session, request.question, history=request.history):
            yield chunk

    return StreamingResponse(event_generator(), media_type='text/event-stream')
