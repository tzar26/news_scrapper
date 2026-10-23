"""Извлечение сущностей (NER) и тональности (Sentiment) через LLM."""

from __future__ import annotations

import json
import logging
from typing import Any

import ollama

from news_scraper.domain.enums import Sentiment
from news_scraper.infra.settings import settings

logger = logging.getLogger(__name__)

MODEL = 'qwen2.5-coder:14b-16k'

EXTRACTOR_PROMPT = """Ты — аналитик. Прочитай текст новости и извлеки из него следующую информацию:
1. Тональность новости (sentiment): выбери строго ОДНО из: "positive", "neutral", "negative".
2. Сущности (entities): найди в тексте компании (ORG), персоны (PER) и страны/локации (LOC).

ПРАВИЛА:
- Ответ должен быть строго в формате JSON.
- Не придумывай сущности, которых нет в тексте.
- Если сущностей нет, верни пустой список [].
- Пример сущности: {{"text": "Лукойл", "type": "ORG"}}.

Пример ответа:
{{
  "sentiment": "neutral",
  "entities": [
    {{"text": "ЦБ РФ", "type": "ORG"}},
    {{"text": "Эльвира Набиуллина", "type": "PER"}}
  ]
}}

Заголовок: {title}
Текст: {text}

JSON:"""


async def extract_info(title: str, text: str) -> tuple[Sentiment, list[dict[str, Any]]]:
    """Извлекает тональность и сущности из текста с помощью LLM.

    Returns:
        Кортеж (Sentiment, список сущностей).
        Если модель ошиблась или вернула невалидный JSON,
        возвращает (Sentiment.UNKNOWN, []).
    """
    short_text = text[:2000].strip()

    prompt = EXTRACTOR_PROMPT.format(title=title, text=short_text)

    client = ollama.AsyncClient(host=settings.ollama_base_url)

    try:
        response = await client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'num_ctx': 4096,
                'temperature': 0.0,
                'format': 'json',  # Ollama обяжет модель вернуть валидный JSON!
            },
            stream=False,
        )

        raw_answer = response['message']['content']
        # Очистка от markdown-оберток (Qwen иногда добавляет ```json)
        clean_json = raw_answer.strip()
        if clean_json.startswith('```json'):
            clean_json = clean_json[7:]
        if clean_json.startswith('```'):
            clean_json = clean_json[3:]
        if clean_json.endswith('```'):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        # На всякий случай ищем первую { и последнюю }
        start_idx = clean_json.find('{')
        end_idx = clean_json.rfind('}')
        if start_idx != -1 and end_idx != -1:
            clean_json = clean_json[start_idx : end_idx + 1]

        data = json.loads(clean_json)

        # Валидация тональности
        sentiment_str = data.get('sentiment', 'neutral').lower()
        try:
            sentiment = Sentiment(sentiment_str)
        except ValueError:
            sentiment = Sentiment.UNKNOWN

        # Валидация сущностей
        entities = data.get('entities', [])
        if not isinstance(entities, list):
            entities = []

        # Оставляем только валидные сущности
        clean_entities = []
        for ent in entities:
            if isinstance(ent, dict) and 'text' in ent and 'type' in ent:
                clean_entities.append({'text': str(ent['text']), 'type': str(ent['type'])})

        return sentiment, clean_entities

    except json.JSONDecodeError:
        logger.warning('LLM returned invalid JSON for title: %s', title[:50])
        return Sentiment.UNKNOWN, []
    except Exception as exc:
        logger.error('Extraction failed: %s', exc)
        return Sentiment.UNKNOWN, []


def extract_info_sync(title: str, text: str) -> tuple[Sentiment, list[dict[str, Any]]]:
    """Синхронная обёртка для вызова из Celery."""
    import asyncio

    return asyncio.run(extract_info(title, text))
