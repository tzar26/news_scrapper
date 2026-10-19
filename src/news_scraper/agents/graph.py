"""LangGraph-агент с tool calling через direct Ollama SDK (plain dict)."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any, Literal

import ollama
from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.agents.state import AgentState
from news_scraper.agents.tools import make_search_tool
from news_scraper.infra.settings import settings

logger = logging.getLogger(__name__)

MODEL = 'qwen2.5-coder:14b-16k'
MAX_ITERATIONS = 6

PLANNER_PROMPT = """Ты — аналитик новостей. Твоя задача — ответить на вопрос,
используя инструмент search_articles для поиска по базе.

Правила:
1. Если нужна информация — вызови ТОЛЬКО ОДИН search_articles с конкретным запросом.
2. После получения результата, если нужно сравнить что-то ещё — вызови search_articles ЕЩЁ РАЗ.
3. Если информации достаточно — сформируй финальный ответ.
4. Финальный ответ должен опираться на факты из статей и содержать ссылки [article_N].
5. Если поиск не дал результатов, скажи об этом честно.

Не выдумывай. Опирайся только на найденные статьи."""


def _tools_to_schema(tools: list) -> list[dict]:
    """Конвертирует LangChain tools в формат Ollama (OpenAI-like)."""
    schema = []
    for t in tools:
        schema.append(
            {
                'type': 'function',
                'function': {
                    'name': t.name,
                    'description': t.description or '',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'Поисковый запрос',
                            },
                        },
                        'required': ['query'],
                    },
                },
            }
        )
    return schema


def _try_parse_tool_calls(content: str) -> list[dict]:
    """Пытается распарсить ОДИН ИЛИ НЕСКОЛЬКО tool call из текстового ответа.

    qwen2.5-coder иногда возвращает несколько JSON-объектов подряд.
    Используем raw_decode для извлечения всех валидных JSON.
    """
    if not content:
        return []

    # Удаляем markdown-обёртки
    text = re.sub(r'```json\n?', '', content)
    text = re.sub(r'```', '', text)

    tool_calls = []
    decoder = json.JSONDecoder()
    pos = 0

    while pos < len(text):
        match = re.search(r'\{', text[pos:])
        if not match:
            break
        start = pos + match.start()
        try:
            obj, index = decoder.raw_decode(text[start:])
            if isinstance(obj, dict) and 'name' in obj and 'arguments' in obj:
                tool_calls.append(
                    {
                        'function': {
                            'name': obj['name'],
                            'arguments': obj['arguments']
                            if isinstance(obj['arguments'], dict)
                            else {},
                        },
                    }
                )
            pos = start + index
        except json.JSONDecodeError:
            pos = start + 1

    return tool_calls


async def _call_planner(state: AgentState, tools: list) -> dict[str, Any]:
    """Планировщик: решает, вызвать tool или дать финальный ответ."""
    client = ollama.AsyncClient(host=settings.ollama_base_url)

    messages: list[dict] = [{'role': 'system', 'content': PLANNER_PROMPT}]
    messages.extend(state['messages'])

    response = await client.chat(
        model=MODEL,
        messages=messages,
        tools=_tools_to_schema(tools),
        options={'num_ctx': 4096, 'temperature': 0.1},  # Снизили температуру для стабильности
    )

    msg = response['message']
    msg_dict = msg.model_dump() if hasattr(msg, 'model_dump') else dict(msg)
    msg_dict.setdefault('role', 'assistant')

    tool_calls = list(msg_dict.get('tool_calls') or [])
    content = msg_dict.get('content') or ''

    # Fallback: qwen2.5-coder отдаёт tool call как JSON в content
    if not tool_calls:
        parsed_calls = _try_parse_tool_calls(content)
        if parsed_calls:
            tool_calls = parsed_calls
            msg_dict['tool_calls'] = tool_calls
            msg_dict['content'] = ''

    # Если не нашли ни tools, ни нормального ответа — это ошибка
    final_answer = None if tool_calls else content.strip()
    if not final_answer and not tool_calls:
        final_answer = 'Не удалось сформировать ответ.'

    return {'messages': [msg_dict], 'final_answer': final_answer}


async def _execute_tools(
    state: AgentState,
    tools_map: dict[str, Any],
) -> dict[str, Any]:
    """Выполняет tool calls из последнего сообщения ассистента."""
    last = state['messages'][-1]
    tool_calls = last.get('tool_calls') or []

    results: list[dict] = []
    for call in tool_calls:
        fn = call.get('function') or {}
        name = fn.get('name')
        raw_args = fn.get('arguments') or {}
        if isinstance(raw_args, str):
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {'query': raw_args}
        else:
            args = dict(raw_args)

        tool = tools_map.get(name)
        if tool is None:
            results.append(
                {
                    'role': 'tool',
                    'content': json.dumps({'error': f'unknown tool: {name}'}),
                }
            )
            continue

        try:
            out = await tool.invoke(args)
        except Exception as exc:
            logger.exception('tool %s failed', name)
            out = json.dumps({'error': str(exc)})

        results.append(
            {
                'role': 'tool',
                'content': str(out),
            }
        )

    return {'messages': results, 'iterations': state['iterations'] + 1}


async def _finalize(state: AgentState) -> dict[str, Any]:
    """Пустая нода-заглушка."""
    return {}


def _should_continue(state: AgentState) -> Literal['tools', 'finalize']:
    """Роутер после planner."""
    if state.get('final_answer'):
        return 'finalize'
    if state['iterations'] >= MAX_ITERATIONS:
        return 'finalize'
    if not state['messages']:
        return 'finalize'
    last = state['messages'][-1]
    if last.get('tool_calls'):
        return 'tools'
    return 'finalize'


async def run_agent(session: AsyncSession, question: str) -> dict[str, Any]:
    """Запускает агента и возвращает финальный ответ."""
    tools = [make_search_tool(session)]
    tools_map = {t.name: t for t in tools}

    async def planner_node(state: AgentState) -> dict[str, Any]:
        return await _call_planner(state, tools)

    async def tools_node(state: AgentState) -> dict[str, Any]:
        return await _execute_tools(state, tools_map)

    async def finalize_node(state: AgentState) -> dict[str, Any]:
        return await _finalize(state)

    graph = StateGraph(AgentState)
    graph.add_node('planner', planner_node)
    graph.add_node('tools', tools_node)
    graph.add_node('finalize', finalize_node)
    graph.add_edge(START, 'planner')
    graph.add_conditional_edges(
        'planner',
        _should_continue,
        {'tools': 'tools', 'finalize': 'finalize'},
    )
    graph.add_edge('tools', 'planner')
    graph.add_edge('finalize', END)

    app = graph.compile()

    initial: AgentState = {
        'question': question,
        'messages': [{'role': 'user', 'content': question}],
        'iterations': 0,
        'final_answer': None,
    }

    langfuse_handler = CallbackHandler()
    config = {'callbacks': [langfuse_handler]}

    result = await app.ainvoke(initial, config=config)
    final = result.get('final_answer') or 'Не удалось сформировать ответ.'

    return {
        'answer': final,
        'iterations': result['iterations'],
        'messages': result['messages'],
    }


async def run_agent_stream(
    session: AsyncSession,
    question: str,
) -> AsyncIterator[str]:
    """Стриминговый запуск агента.

    Выдаёт SSE-форматированные строки:
    - data: {"type": "status", "content": "..."} — статусы шагов.
    - data: {"type": "token", "content": "..."} — токены финального ответа.
    - data: {"type": "end"} — завершение.
    """
    tools = [make_search_tool(session)]
    tools_map = {t.name: t for t in tools}

    async def planner_node(state: AgentState) -> dict[str, Any]:
        return await _call_planner(state, tools)

    async def tools_node(state: AgentState) -> dict[str, Any]:
        return await _execute_tools(state, tools_map)

    async def finalize_node(state: AgentState) -> dict[str, Any]:
        return await _finalize(state)

    graph = StateGraph(AgentState)
    graph.add_node('planner', planner_node)
    graph.add_node('tools', tools_node)
    graph.add_node('finalize', finalize_node)
    graph.add_edge(START, 'planner')
    graph.add_conditional_edges(
        'planner',
        _should_continue,
        {'tools': 'tools', 'finalize': 'finalize'},
    )
    graph.add_edge('tools', 'planner')
    graph.add_edge('finalize', END)

    app = graph.compile()

    initial: AgentState = {
        'question': question,
        'messages': [{'role': 'user', 'content': question}],
        'iterations': 0,
        'final_answer': None,
    }

    yield 'data: {"type": "status", "content": "🤔 Агент планирует запрос..."}\n\n'

    try:
        async for event in app.astream_events(initial, version='v2'):
            kind = event['event']

            if kind == 'on_chain_start' and event.get('name') == 'tools':
                yield 'data: {"type": "status", "content": "🔍 Ищу статьи в базе..."}\n\n'

            if kind == 'on_chain_end' and event.get('name') == 'planner':
                output = event['data'].get('output', {})
                if output.get('final_answer'):
                    final_text = output['final_answer']
                    yield 'data: {"type": "status", "content": "✍️ Формирую ответ..."}\n\n'

                    import asyncio

                    words = final_text.split(' ')
                    for i, word in enumerate(words):
                        chunk = word + (' ' if i < len(words) - 1 else '')
                        payload = json.dumps({'type': 'token', 'content': chunk})
                        yield f'data: {payload}\n\n'
                        await asyncio.sleep(0.04)  # Небольшая пауза для эффекта печатной машинки

                    # Безопасно завершаем без запроса несуществующих полей
                    yield 'data: {"type": "end"}\n\n'
                    return

    except Exception as exc:
        logger.exception('Error during agent streaming')
        error_msg = json.dumps({'type': 'error', 'content': str(exc)})
        yield f'data: {error_msg}\n\n'
