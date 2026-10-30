from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AgentRequest(BaseModel):
    """Запрос к LangGraph-агенту."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    question: str = Field(
        min_length=1,
        max_length=1000,
        description='Вопрос на естественном языке',
        examples=['Сравни ситуацию с нефтью и газом в России'],
    )
    history: list[dict] | None = Field(
        default=None, description='История прошлых сообщений [{"role": "user", "content": "..."}]'
    )


class AgentResponse(BaseModel):
    """Ответ агента."""

    answer: str = Field(description='Сформированный ответ')
    iterations: int = Field(description='Сколько шагов сделал агент')
