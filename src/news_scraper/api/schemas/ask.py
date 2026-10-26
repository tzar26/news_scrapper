from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """Запрос к RAG-эндпоинту."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    question: str = Field(
        min_length=1,
        max_length=1000,
        description='Вопрос на естественном языке',
        examples=['Что происходит с нефтью?'],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description='Сколько уникальных историй подать в контекст',
    )
    rerank: bool = Field(
        default=False,
        description='Применить cross-encoder reranking после retrieval',
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


class SourceRefResponse(BaseModel):
    """Источник, на который ссылается ответ."""

    id: int = Field(description='ID статьи')
    url: str = Field(description='URL статьи')
    title: str = Field(description='Заголовок статьи')


class AskResponse(BaseModel):
    """Ответ RAG-пайплайна."""

    answer: str = Field(description='Текст ответа с цитатами [article_N]')
    sources: list[SourceRefResponse] = Field(
        default_factory=list,
        description='Источники, упомянутые в ответе',
    )
