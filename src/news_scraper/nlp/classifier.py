"""Классификатор статей на основе LLM (Zero-Shot)."""

from __future__ import annotations

import logging

import ollama

from news_scraper.domain.enums import Category
from news_scraper.infra.settings import settings

logger = logging.getLogger(__name__)

MODEL = 'qwen2.5-coder:14b-16k'

# Список категорий для промпта (включаем OTHER, чтобы модель не ленилась)
ALLOWED_CATEGORIES = [
    'politics',
    'business',
    'conflicts',
    'energy',
    'key_rates',
    'technology',
    'auto',
    'economy',
    'currency',
    'stocks',
    'entertainment',
    'sports',
    'culture',
    'health',
    'environment',
    'other',
]

CLASSIFIER_PROMPT = """Ты — аналитик новостей. Твоя задача — определить категорию статьи.
Прочитай заголовок и текст, затем выбери РОВНО ОДНУ категорию из списка ниже.
СПИСОК КАТЕГОРИЙ:
- politics: выборы, законы, заявления политиков, международные отношения.
- business: компании, сделки, рынки, инвестиции.
- conflicts: войны, санкции, военные действия, теракты, криминал, ДТП, ЧП.
- energy: нефть, газ, уголь, ОПЕК, добыча, поставки энергоносителей.
- key_rates: ключевая ставка, решения ЦБ по ставке, инфляция.
- technology: ИТ, новые технологии, гаджеты, ИИ, кибербезопасность.
- auto: производство автомобилей, автоконцерны, новые модели авто. (Внимание: ДТП относится к conflicts).
- economy: макроэкономика, ВВП, бюджет, безработица, экономические прогнозы.
- currency: курсы валют, доллар, евро, юань, рубль.
- stocks: фондовый рынок, акции, облигации, индексы.
- entertainment: шоу-бизнес, кино, знаменитости, музыка.
- sports: спорт, соревнования, олимпиады, результаты матчей.
- culture: искусство, выставки, театр, литература, религия.
- health: медицина, вакцинация, болезни, здравоохранение.
- environment: экология, погода, климат, изменения климата, природа.
- other: всё, что не подходит под остальные категории.
ПРАВИЛА:
1. Если статья ни под одну категорию не подходит, верни "other".
2. Ответ должен быть ТОЛЬКО названием категории на английском, без кавычек и лишних слов.
3. Не придумывай новые категории. Если сомневаешься — выбирай "other".
Заголовок: {title}
Текст: {text}
Категория:"""


async def classify_article(title: str, text: str) -> Category:
    """Определяет категорию статьи с помощью LLM.

    Args:
        title: заголовок статьи.
        text: текст статьи (или summary).

    Returns:
        Category из domain/enums.py. Если модель ошиблась или ответила
        мусором, возвращает Category.OTHER.
    """
    # Обрезаем текст, чтобы не раздувать контекст (модели хватает первых 2000 знаков)
    short_text = text[:2000].strip()

    prompt = CLASSIFIER_PROMPT.format(
        allowed_categories=', '.join(ALLOWED_CATEGORIES),
        title=title,
        text=short_text,
    )

    client = ollama.AsyncClient(host=settings.ollama_base_url)

    try:
        response = await client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'num_ctx': 4096,
                'temperature': 0.0,  # Строгая детерминация
            },
            stream=False,
        )

        raw_answer = response['message']['content'].strip().lower()

        # Убираем кавычки и точки, если модель их поставила
        clean_answer = raw_answer.strip('"\'.,` ')

        # Пытаемся привести к нашему Enum
        try:
            return Category(clean_answer)
        except ValueError:
            logger.warning(
                'LLM returned invalid category "%s" for title: %s', raw_answer, title[:50]
            )
            return Category.OTHER

    except Exception as exc:
        logger.error('Classification failed: %s', exc)
        return Category.OTHER


# Синхронная обёртка для удобства в Celery
def classify_article_sync(title: str, text: str) -> Category:
    """Синхронная обёртка для вызова из Celery."""
    import asyncio

    return asyncio.run(classify_article(title, text))
