from __future__ import annotations

from enum import StrEnum


class Country(StrEnum):
    """
    Enum representing different countries.
    """

    USA = 'USA'
    CANADA = 'Canada'
    MEXICO = 'Mexico'
    GERMANY = 'Germany'
    FRANCE = 'France'
    JAPAN = 'Japan'
    CHINA = 'China'
    INDIA = 'India'
    UK = 'UK'
    AUSTRALIA = 'Australia'
    RUSSIA = 'Russia'


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
