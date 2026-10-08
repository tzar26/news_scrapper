from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleResponse(BaseModel):
    """Публичное представление статьи для API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description='Идентификатор статьи')
    url: str = Field(description='URL статьи')
    title: str = Field(description='Заголовок статьи')
    source: str = Field(description='Источник статьи')
    country: str = Field(description='Страна статьи')
    category: str = Field(description='Категория статьи')
    published_at: datetime = Field(description='Дата публикации статьи')
    summary: str | None = Field(description='Краткое описание статьи', default=None)


class ArticleDetailResponse(ArticleResponse):
    """Детальное представление статьи, включая полный текст."""

    text: str = Field(description='Полный текст статьи')


class ArticlesPage(BaseModel):
    """Постраничный ответ со списком статей."""

    items: list[ArticleResponse] = Field(description='Список статей на текущей странице')
    total: int = Field(description='Общее число статей под фильтрами')
    limit: int = Field(description='Количество статей на странице')
    offset: int = Field(description='Смещение для получения текущей страницы')
