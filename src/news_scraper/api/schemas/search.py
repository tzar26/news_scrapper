from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    """Запрос семантического поиска."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    query: str = Field(
        min_length=1,
        max_length=500,
        description='Поисковый запрос',
        examples=['ключевая ставка ЦБ'],
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description='Сколько уникальных историй вернуть',
    )
    days_ago: int | None = Field(
        default=None,
        ge=1,
        le=30,
        description='Искать статьи за последние N дней. Если None — за всё время.',
    )
    use_hyde: bool = Field(
        default=False,
        description='Применить HyDE (генерация гипотетического ответа перед поиском)',
    )


class RelatedArticleResponse(BaseModel):
    """Перепечатка (другой источник, та же история)."""

    id: int = Field(description='ID статьи')
    url: str = Field(description='URL статьи')
    source: str = Field(description='Источник')


class SearchResultResponse(BaseModel):
    """Одна уникальная история в результатах поиска."""

    representative_id: int = Field(description='ID представительской статьи')
    url: str = Field(description='URL представительской статьи')
    title: str = Field(description='Заголовок')
    text: str = Field(description='Текст статьи (обрезка до 500 символов)')
    rrf_score: float = Field(description='RRF-оценка релевантности')
    related: list[RelatedArticleResponse] = Field(
        default_factory=list,
        description='Перепечатки этой же истории',
    )


class SearchResponse(BaseModel):
    """Ответ семантического поиска."""

    query: str = Field(description='Исходный запрос')
    results: list[SearchResultResponse] = Field(description='Найденные истории')
