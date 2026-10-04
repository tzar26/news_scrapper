# Pydantic (RawNewsItem, SentimentResult, ...)
from enum import StrEnum

class Country(StrEnum):
    USA = "usa"
    RUSSIA = "russia"
    CHINA = "china"
    OTHER = "other"

class Sentiment(StrEnum):
    """Тональность новости."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class Category(StrEnum):
    """Тематическая категория новости."""

    POLITICS = "politics"
    CURRENCY = "currency"
    STOCKS = "stocks"
    KEY_RATES = "key_rates"
    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    BUSINESS = "business"
    OTHER = "other"


from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime
from typing import Optional

class RawNewsItem(BaseModel):
    url: HttpUrl
    title: str
    source: str
    country: Country
    category: Category = Category.OTHER
    published_at: datetime
    text: str
    summary: Optional[str]

    class Config:
        extra = "forbid"
        str_strip_whitespace = True

    @validator('published_at', pre=True)
    def check_timezone(cls, value: datetime):
        if value.tzinfo is None:
            raise ValueError("Published_at must have a timezone")
        return value
