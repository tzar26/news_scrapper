"""Перечисления предметной области: страна, тональность, категория."""

from __future__ import annotations

from enum import StrEnum


class Country(StrEnum):
    """Страна, к которой относится новость."""

    USA = 'usa'
    RUSSIA = 'russia'
    CHINA = 'china'
    OTHER = 'other'


class Sentiment(StrEnum):
    """Тональность новости."""

    POSITIVE = 'positive'
    NEUTRAL = 'neutral'
    NEGATIVE = 'negative'


class Category(StrEnum):
    """Тематическая категория новости."""

    # Темы проекта
    POLITICS = 'politics'
    BUSINESS = 'business'
    CONFLICTS = 'conflicts'
    ENERGY = 'energy'  # добыча ископаемых
    KEY_RATES = 'key_rates'  # ключевая ставка
    TECHNOLOGY = 'technology'  # ИТ
    AUTO = 'auto'  # автомобилестроение

    # Финансы и рынки
    ECONOMY = 'economy'
    CURRENCY = 'currency'
    STOCKS = 'stocks'

    # Общие рубрики из RSS
    ENTERTAINMENT = 'entertainment'
    SPORTS = 'sports'
    CULTURE = 'culture'
    HEALTH = 'health'
    ENVIRONMENT = 'environment'

    OTHER = 'other'
