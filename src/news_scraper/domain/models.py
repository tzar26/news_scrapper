from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from .enums import Category, Country


class RawNewsItem(BaseModel):
    """Raw news item model."""

    url: HttpUrl = Field(description='URL of the news item')
    title: Annotated[str, Field(min_length=1, max_length=500)] = Field(
        description='Title of the news item'
    )
    source: str = Field(description='Source of the news item')
    country: Country = Field(description='Country of the news item')
    category: Category = Field(default=Category.OTHER, description='Category of the news item')
    published_at: datetime = Field(description='Publication date and time of the news item')
    text: str = Field(description='Text of the news item')
    summary: str | None = Field(default=None, description='Summary of the news item')

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    @model_validator(mode='after')
    @classmethod
    def check_timezone(cls, value):
        if value.published_at.tzinfo is None:
            raise ValueError('Published_at must have a timezone')
        return value
