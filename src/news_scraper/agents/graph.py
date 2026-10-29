"""LangGraph-агент с tool calling через direct Ollama SDK (plain dict)."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any, Literal

import ollama
from langchain_core.runnables import RunnableConfig
from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.agents.state import AgentState
from news_scraper.agents.tools import (
    make_entity_tool,
    make_market_impact_tool,
    make_metrics_tool,
    make_search_tool,
)
from news_scraper.infra.settings import settings

logger = logging.getLogger(__name__)

MODEL = 'qwen2.5-coder:14b-16k'
MAX_ITERATIONS = 6

PLANNER_PROMPT = """Ты — аналитик новостей. Твоя задача — ответить на вопрос,
используя инструмент search_articles для поиска по базе.

Правила:
1. Если нужна информация — вызови ТОЛЬКО ОДИН search_articles с конкретным запросом.
2. После получения результата, если нужно сравнить что-то ещё — вызови search_articles ЕЩЁ РАЗ.
2.1. Если пользователь упоминает временной период (например, "за 3 дня", "за неделю"), передай его в параметре days_ago (целое число дней). "За неделю" = 7, "за сутки" = 1.
3. Если информации достаточно — сформируй финальный ответ.
4. Финальный ответ должен опираться на факты из статей и содержать ссылки [article_N].
5. Если поиск не дал результатов, скажи об этом честно.
6. Для получения статистики (сколько статей, какие категории) используй инструмент get_metrics.
7. Инструмент get_metrics возвращает текстовую статистику. Используй её, чтобы ответить на вопрос пользователя.
8. Для поиска новостей про конкретную компанию или персону используй search_by_entity (можно указать sentiment: positive/negative/neutral).
9. Для оценки новостного фона в секторах используй get_market_impact (например, "какие сектора сейчас в фокусе?").

Не выдумывай. Опирайся только на найденные статьи."""


def _tools_to_schema(tools: list) -> list[dict]:
    """Конвертирует LangChain tools в формат Ollama (OpenAI-like)."""
    schema = []
    for t in tools:
        schema.append(
            {
                'type': 'function',
                'function': {
                    'name': getattr(t, 'name', 'unknown'),
                    'description': t.description or '',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'Поисковый запрос',
                            },
                            'days_ago': {
                                'type': 'integer',
                                'description': 'Искать статьи за последние N дней (опционально)',
                            },
                            'group_by': {
                                'type': 'string',
                                'description': 'Для get_metrics: category, country, source',
                            },
                            'entity': {
                                'type': 'string',
                                'description': 'Название компании, персоны или страны (для search_by_entity)',
                            },
                            'sentiment': {
                                'type': 'string',
                                'description': 'Тональность: positive, negative или neutral (для search_by_entity)',
                            },
                            'category': {
                                'type': 'string',
                                'description': 'Категория новостей: energy, politics, economy, technology, auto, retail и т.д. (для get_sentiment)',
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
        if not isinstance(name, str):
            continue
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
            logger.exception('Tool %s failed with args=%r', name, args)
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
    tools = [
        make_search_tool(session),
        make_metrics_tool(session),
        make_entity_tool(session),
        make_market_impact_tool(session),
    ]
    tools_map = {getattr(t, 'name', 'unknown'): t for t in tools}

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
    config: RunnableConfig = {'callbacks': [langfuse_handler]}

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

    Выдаёт SSE-форматированные строки.
    Использует stream_mode="values" для надёжного перехвата состояний.
    """
    tools = [
        make_search_tool(session),
        make_metrics_tool(session),
        make_entity_tool(session),
        make_market_impact_tool(session),
    ]
    tools_map = {getattr(t, 'name', 'unknown'): t for t in tools}

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

    langfuse_handler = CallbackHandler()
    config: RunnableConfig = {'callbacks': [langfuse_handler]}

    try:
        # Используем stream_mode="values" — на каждом шаге отдаётся полный State
        async for state in app.astream(initial, config=config, stream_mode='values'):
            messages = state.get('messages', [])
            if not messages:
                continue

            last_msg = messages[-1]

            # Если последнее сообщение — это вызов инструмента
            if last_msg.get('tool_calls'):
                for tc in last_msg['tool_calls']:
                    tool_name = tc['function'].get('name', 'unknown')
                    raw_args = tc['function'].get('arguments', {})

                    parsed_args: dict[str, Any] = {}
                    if isinstance(raw_args, str):
                        try:
                            parsed_args = json.loads(raw_args)
                        except Exception:
                            parsed_args = {}
                    elif isinstance(raw_args, dict):
                        parsed_args = raw_args

                    # Формируем красивую подпись в зависимости от инструмента
                    try:
                        if tool_name == 'search_articles':
                            query = parsed_args.get('query', '')
                            status_msg = f'🔍 Ищу статьи по запросу: «{query}»'
                        elif tool_name == 'search_by_entity':
                            entity = parsed_args.get('entity', '')
                            sentiment = parsed_args.get('sentiment')
                            sent_str = f' (тональность: {sentiment})' if sentiment else ''
                            status_msg = f'🏢 Ищу новости про: «{entity}»{sent_str}'
                        elif tool_name == 'get_metrics':
                            group_by = parsed_args.get('group_by', 'category')
                            days = parsed_args.get('days_ago')
                            days_str = f' за последние {days} дн.' if days else ''
                            status_msg = f'📊 Считаю статистику по «{group_by}»{days_str}'
                        elif tool_name == 'get_market_impact':
                            days = parsed_args.get('days_ago')
                            days_str = f' за {days} дн.' if days else ''
                            status_msg = f'📊 Оцениваю новостной фон{days_str}'
                        else:
                            status_msg = f'🛠️ Вызываю {tool_name}...'
                    except Exception:
                        status_msg = f'🛠️ Вызываю {tool_name}...'

                    yield f'data: {json.dumps({"type": "status", "content": status_msg}, ensure_ascii=False)}\n\n'

            # Если появился финальный ответ
            final_answer = state.get('final_answer')
            if final_answer:
                yield 'data: {"type": "status", "content": "✍️ Формирую ответ..."}\n\n'

                # Эмуляция стриминга по словам
                words = final_answer.split(' ')
                for i, word in enumerate(words):
                    chunk = word + (' ' if i < len(words) - 1 else '')
                    payload = json.dumps({'type': 'token', 'content': chunk})
                    yield f'data: {payload}\n\n'
                    await asyncio.sleep(0.03)

                yield 'data: {"type": "end"}\n\n'
                return

    except Exception as exc:
        logger.exception('Error during agent streaming')
        error_msg = json.dumps({'type': 'error', 'content': str(exc)})
        yield f'data: {error_msg}\n\n'
