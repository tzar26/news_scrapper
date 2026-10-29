"""Оценка качества генерации (Faithfulness, Answer Relevance) через LLM."""

from __future__ import annotations

import json
import logging
from typing import Any

import ollama

from news_scraper.infra.settings import settings

logger = logging.getLogger(__name__)

MODEL = 'qwen2.5-coder:14b-16k'

JUDGE_PROMPT = """Ты — эксперт по оценке качества AI-ответов. Оцени ответ ассистента по двум критериям:

1. Faithfulness (Верность контексту): все ли факты в ответе подтверждаются предоставленным контекстом? Если ответ содержит информацию, которой нет в контексте — это галлюцинация, ставь низкий балл.
2. Answer Relevance (Релевантность): ответил ли ассистент именно на заданный вопрос? Если ответ уходит в сторону или не отвечает на вопрос — ставь низкий балл.

Оцени каждый критерий от 0.0 до 1.0, где 1.0 — идеально.

Вопрос: {question}
Контекст: {context}
Ответ ассистента: {answer}

Ответь строго в формате JSON:
{{
  "faithfulness": 0.9,
  "answer_relevance": 0.8,
  "reasoning": "Краткое пояснение оценки"
}}
"""


async def evaluate_answer(
    question: str,
    answer: str,
    contexts: list[str],
) -> dict[str, Any]:
    """Оценивает качество ответа RAG-системы.

    Args:
        question: вопрос пользователя.
        answer: ответ LLM.
        contexts: список текстов найденных статей.

    Returns:
        Dict с ключами faithfulness, answer_relevance, reasoning.
        Если оценка не удалась, возвращает пустой dict.
    """
    # Объединяем контексты в один текст (ограничиваем длину)
    context_text = '\n\n'.join(contexts)[:4000]

    prompt = JUDGE_PROMPT.format(
        question=question,
        context=context_text,
        answer=answer,
    )

    client = ollama.AsyncClient(host=settings.ollama_base_url)

    try:
        response = await client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'num_ctx': 4096,
                'temperature': 0.0,
                'format': 'json',
            },
            stream=False,
        )

        raw = response['message']['content']

        # Очистка от markdown
        clean = raw.strip()
        if clean.startswith('```json'):
            clean = clean[7:]
        if clean.endswith('```'):
            clean = clean[:-3]
        clean = clean.strip()

        data = json.loads(clean)

        # Валидация
        if not isinstance(data, dict):
            return {}

        faithfulness = data.get('faithfulness', 0.0)
        relevance = data.get('answer_relevance', 0.0)

        # Приводим к float и ограничиваем [0, 1]
        try:
            faithfulness = max(0.0, min(1.0, float(faithfulness)))
            relevance = max(0.0, min(1.0, float(relevance)))
        except (ValueError, TypeError):
            faithfulness = 0.0
            relevance = 0.0

        return {
            'faithfulness': faithfulness,
            'answer_relevance': relevance,
            'reasoning': data.get('reasoning', ''),
        }

    except Exception as exc:
        logger.error('Evaluation failed: %s', exc)
        return {}


def evaluate_answer_sync(question: str, answer: str, contexts: list[str]) -> dict[str, Any]:
    """Синхронная обёртка."""
    import asyncio

    return asyncio.run(evaluate_answer(question, answer, contexts))
