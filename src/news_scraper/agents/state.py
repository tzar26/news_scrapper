"""State для LangGraph-агента (plain dict messages, без LangChain)."""

from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict


class AgentState(TypedDict):
    """Состояние агента между шагами.

    messages — список dict в формате Ollama:
        {'role': 'user'|'assistant'|'tool'|'system',
         'content': str,
         'tool_calls': list | None}

    Annotated с operator.add — LangGraph будет складывать
    списки сообщений, а не перезаписывать.
    """

    question: str
    history: list[dict]
    messages: Annotated[list[dict], add]
    iterations: int
    final_answer: str | None
