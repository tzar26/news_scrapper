"""HyDE (Hypothetical Document Embeddings) для улучшения RAG."""

from __future__ import annotations

import logging

import ollama

from news_scraper.infra.settings import settings

logger = logging.getLogger(__name__)

MODEL = 'qwen2.5-coder:14b-16k'

HYDE_PROMPT = """Напиши короткий абзац (2-3 предложения) от лица аналитика,
который отвечает на следующий вопрос. Используй профессиональную лексику,
связанную с экономикой и новостями. Не используй вводные слова (типа "ответ:"),
просто напиши сам текст.

Вопрос: {question}
Текст:"""


async def generate_hypothetical_answer(question: str) -> str:
    """Генерирует гипотетический ответ на вопрос для улучшения поиска.

    Args:
        question: исходный вопрос пользователя.

    Returns:
        Сгенерированный текст. Если LLM недоступна, возвращает исходный вопрос.
    """
    client = ollama.AsyncClient(host=settings.ollama_base_url)

    try:
        response = await client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': HYDE_PROMPT.format(question=question)}],
            options={
                'num_ctx': 4096,
                'temperature': 0.3,  # Небольшая вариативность для синонимов
            },
            stream=False,
        )

        hypothetical_text = response['message']['content'].strip()
        logger.debug('HyDE generated: %s', hypothetical_text[:100])
        return hypothetical_text

    except Exception as exc:
        logger.warning('HyDE generation failed, falling back to original query: %s', exc)
        return question
