"""Сравнение ChatOllama (LangChain) vs ollama.AsyncClient на одинаковом промпте."""

from __future__ import annotations

import asyncio
import time

import ollama
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

OLLAMA_URL = 'http://192.168.0.118:11434'
MODEL = 'qwen2.5-coder:14b-16k'
PROMPT = 'Что нового с ключевой ставкой ЦБ? Ответь одним предложением.'


async def via_langchain() -> tuple[float, str]:
    """Через ChatOllama."""
    llm = ChatOllama(
        model=MODEL,
        temperature=0.1,
        num_ctx=4096,
        base_url=OLLAMA_URL,
    )
    start = time.monotonic()
    response = await llm.ainvoke([HumanMessage(content=PROMPT)])
    return time.monotonic() - start, response.content


async def via_ollama() -> tuple[float, str]:
    """Через прямой ollama.AsyncClient."""
    client = ollama.AsyncClient(host=OLLAMA_URL)
    start = time.monotonic()
    response = await client.chat(
        model=MODEL,
        messages=[{'role': 'user', 'content': PROMPT}],
        options={'num_ctx': 4096, 'temperature': 0.3},
    )
    return time.monotonic() - start, response['message']['content']


async def main() -> None:
    """Прогон: сначала прогреваем, потом сравниваем."""
    print('Прогрев...')
    await via_ollama()
    await via_langchain()

    print('\n=== Сравнение ===')
    for name, fn in [('ollama (raw)', via_ollama), ('langchain', via_langchain)]:
        elapsed, content = await fn()
        print(f'\n{name}: {elapsed:.2f}s')
        print(f'  ответ: {content[:200]}')


if __name__ == '__main__':
    asyncio.run(main())
