from __future__ import annotations

from enum import StrEnum


class Country(StrEnum):
    USA = 'usa'
    RUSSIA = 'russia'
    CHINA = 'china'
    OTHER = 'other'


class Sentiment(StrEnum):
    POSITIVE = 'positive'
    NEGATIVE = 'negative'
    NEUTRAL = 'neutral'


class Category(StrEnum):
    POLITICS = 'politics'
    ECONOMY = 'economy'
    TECHNOLOGY = 'technology'
    CULTURE = 'culture'
    SPORTS = 'sports'
    HEALTH = 'health'
    ENVIRONMENT = 'environment'
    BUSINESS = 'business'
    OTHER = 'other'
