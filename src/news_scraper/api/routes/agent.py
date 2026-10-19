from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.agents.graph import run_agent
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
    result = await run_agent(session, request.question)
    return AgentResponse(
        answer=result['answer'],
        iterations=result['iterations'],
    )
