"""Оценка влияния новости на рынок (Market Impact)."""

from __future__ import annotations

import json
import logging
from typing import Any

import ollama

from news_scraper.infra.settings import settings

logger = logging.getLogger(__name__)

MODEL = 'qwen2.5-coder:14b-16k'

IMPACT_PROMPT = """Ты — профессиональный трейдер на российском фондовом рынке.
Прочитай новость и определи её тип, масштаб и влияние на акции.

ТИП (type):
- "event": конкретное событие (отчет, санкции, сделка, заявление регулятора).
- "overview": обзорная статья, дайджест, мнение аналитика, сезонная заметка.

МАСШТАБ (importance):
- "high": влияет на весь рынок или крупный сектор (санкции, ставка ЦБ, крупные сделки).
- "medium": влияет на конкретную компанию или узкий сегмент (дефолт эмитента).
- "low": локальные новости, спорт, погода, светская хроника, региональные законы.

ГЕОГРАФИЯ (target_market):
- "ru", "us", "eu", "global". Для чего важен этот инфоповод.

ГЛАВНЫЙ СЕКТОР (main_sector):
- Выбери ОДИН главный сектор из: energy, technology, retail, stocks, currency, politics, economy.
- Если новость не влияет на рынки (importance=low или type=overview) — выбери "none".

НАПРАВЛЕНИЕ (direction):
- "bullish" (позитив), "bearish" (негатив), "neutral" (не влияет).

ПРАВИЛА:
- Если новость про дефолт одной компании (не Газпром/Сбер) — importance: medium, main_sector: stocks, direction: bearish.
- Если новость про локальные боевые действия (без эскалации) — importance: low, main_sector: none.
- Если новость про «намерения» (без подписанных контрактов) — importance: low, main_sector: none.
- Если новость про спорт/погоду/культуру — importance: low, main_sector: none.

Ответ должен быть строго в формате JSON:
{{
  "type": "event",
  "target_market": "ru",
  "importance": "high",
  "main_sector": "energy",
  "direction": "bullish"
}}

Заголовок: {title}
Текст: {text}

JSON:"""


async def extract_market_impact(title: str, text: str) -> dict[str, Any]:
    """Определяет влияние новости на рынок."""
    short_text = text[:3000].strip()
    prompt = IMPACT_PROMPT.format(title=title, text=short_text)

    client = ollama.AsyncClient(host=settings.ollama_base_url)

    try:
        response = await client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={'num_ctx': 4096, 'temperature': 0.0, 'format': 'json'},
            stream=False,
        )

        raw = response['message']['content']
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

        allowed_importance = {'high', 'medium', 'low'}
        allowed_sectors = {
            'energy',
            'technology',
            'retail',
            'stocks',
            'currency',
            'politics',
            'economy',
            'none',
        }
        allowed_dirs = {'bullish', 'bearish', 'neutral'}

        importance = data.get('importance', 'low')
        if importance not in allowed_importance:
            importance = 'low'

        sector = data.get('main_sector', 'none')
        if sector not in allowed_sectors:
            sector = 'none'

        direction = data.get('direction', 'neutral')
        if direction not in allowed_dirs:
            direction = 'neutral'

        return {
            'type': data.get('type', 'event'),
            'target_market': data.get('target_market', 'ru'),
            'importance': importance,
            'main_sector': sector,
            'direction': direction,
        }

    except Exception as exc:
        logger.error('Impact extraction failed: %s', exc)
        return {}


def extract_market_impact_sync(title: str, text: str) -> dict[str, Any]:
    """Синхронная обёртка."""
    import asyncio

    return asyncio.run(extract_market_impact(title, text))
