from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CountItem(BaseModel):
    """Одна строка агрегата: значение + количество."""

    key: str = Field(description='Значение группировки')
    count: int = Field(description='Количество статей')


class StatsResponse(BaseModel):
    """Агрегированная статистика по всем статьям."""

    total_articles: int = Field(description='Всего статей')
    by_country: list[CountItem] = Field(description='По странам')
    by_source: list[CountItem] = Field(description='По источникам')
    by_category: list[CountItem] = Field(description='По категориям')
    latest_published_at: datetime | None = Field(
        default=None,
        description='Самая свежая дата публикации',
    )
    earliest_published_at: datetime | None = Field(
        default=None,
        description='Самая старая дата публикации',
    )
