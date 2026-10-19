# ADR-013: LangGraph-агент с tool calling

Дата: 2026-10-19
Статус: принято

## Контекст

Текущий `/ask` — линейный RAG (retrieval → LLM). Для простых
вопросов этого достаточно. Но для сложных сценариев
(«сравни X и Y», «что общего между A и B») нужно:
- Несколько поисков с разными запросами.
- Агрегация результатов.
- Многошаговое рассуждение.

## Решение

**LangGraph агент в `agents/`.** Архитектура:

### State

```python
class AgentState(TypedDict):
    question: str
    messages: list[BaseMessage]       # история (tool calls, результаты)
    final_answer: str | None
    iterations: int                   # счётчик шагов (защита от зацикливания)
