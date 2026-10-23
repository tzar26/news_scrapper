"""Tools для LangGraph-агента."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.rag.retriever import search

logger = logging.getLogger(__name__)


class SearchArticlesTool:
    """Инструмент поиска статей."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.name = 'search_articles'
        self.description = 'Ищет статьи в базе по текстовому запросу.'

    async def invoke(self, args: dict[str, Any]) -> str:
        """Выполняет поиск статей.

        Args:
            args: dict с ключами 'query' (str) и опционально 'days_ago' (int).
        """
        query = args.get('query')
        # Защита: если LLM передала dict вместо строки или пустоту
        if not isinstance(query, str) or not query.strip():
            return 'Ошибка: для поиска статей необходимо передать корректный текстовый запрос в поле query.'

        # Извлекаем days_ago, если агент его передал
        try:
            days_ago = args.get('days_ago')
            if days_ago is not None:
                days_ago = int(days_ago)
        except (ValueError, TypeError):
            days_ago = None

        try:
            results = await search(self._session, query, top_k=5, days_ago=days_ago)
            return json.dumps(
                [
                    {
                        'id': r.representative_id,
                        'title': r.title,
                        'text': r.text[:300],
                    }
                    for r in results
                ],
                ensure_ascii=False,
            )
        except Exception as exc:  # noqa: BLE001
            return json.dumps({'error': str(exc)})


def make_search_tool(session: AsyncSession) -> SearchArticlesTool:
    """Создаёт инструмент поиска, привязанный к сессии БД."""
    return SearchArticlesTool(session)


class GetMetricsTool:
    """Инструмент для получения агрегированной статистики по базе."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.name = 'get_metrics'
        self.description = (
            'Возвращает статистику по статьям: количество по категориям, странам или источникам. '
            'Можно фильтровать по временному периоду (days_ago).'
        )

    async def invoke(self, args: dict[str, Any]) -> str:
        """Получает метрики.

        Args:
            args: dict с ключами:
                - group_by (str): 'category', 'country', 'source'.
                - days_ago (int, optional): фильтр по свежести.
        """
        from news_scraper.db.models import Article

        group_by = args.get('group_by', 'category')
        try:
            days_ago = args.get('days_ago')
            if days_ago is not None:
                days_ago = int(days_ago)
        except (ValueError, TypeError):
            days_ago = None

        logger.info('get_metrics called with group_by=%r, days_ago=%r', group_by, days_ago)

        # Выбираем колонку для группировки
        if group_by == 'country':
            col = Article.country
        elif group_by == 'source':
            col = Article.source
        else:
            col = Article.category_predicted  # type: ignore[assignment]
        stmt = select(col, func.count()).group_by(col).order_by(func.count().desc()).limit(10)

        # Применяем фильтр по времени
        if days_ago is not None:
            cutoff = datetime.now(UTC) - timedelta(days=days_ago)
            stmt = stmt.where(Article.published_at >= cutoff)

        result = await self._session.execute(stmt)
        rows = result.all()

        if not rows:
            return 'За указанный период статей не найдено.'

        # Формируем человекочитаемый ответ вместо JSON!
        lines = [
            f'Статистика по полю "{group_by}" (за последние {days_ago} дн.):'
            if days_ago
            else f'Статистика по полю "{group_by}":'
        ]
        for row in rows:
            key = row[0] if row[0] is not None else 'unclassified'
            lines.append(f'- {key}: {row[1]} шт.')

        return '\n'.join(lines)


def make_metrics_tool(session: AsyncSession) -> GetMetricsTool:
    """Создаёт инструмент метрик, привязанный к сессии БД."""
    return GetMetricsTool(session)


class SearchByEntityTool:
    """Инструмент для поиска статей по упомянутой сущности и тональности."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.name = 'search_by_entity'
        self.description = (
            'Ищет статьи, в которых упоминается конкретная компания, персона или страна. '
            'Можно фильтровать по тональности (positive, negative, neutral).'
        )

    async def invoke(self, args: dict[str, Any]) -> str:
        """Выполняет поиск по сущности.

        Args:
            args: dict с ключами:
                - entity (str): Название компании, персоны или страны.
                - sentiment (str, optional): 'positive', 'negative', 'neutral'.
        """
        from sqlalchemy import select

        from news_scraper.db.models import Article

        entity = args.get('entity')
        sentiment = args.get('sentiment')

        if not isinstance(entity, str) or not entity.strip():
            return 'Ошибка: для поиска по сущности необходимо передать название в поле entity.'

        # Ищем в JSONB-поле entities.
        # Используем оператор @> для поиска вхождения словаря {"text": entity}
        # (Регистрозависимый поиск. Если нужно регистронезависимо, можно перевести в lower, но
        # в JSONB это сложнее, поэтому пока так).
        stmt = select(Article).where(Article.entities.contains([{'text': entity}]))

        if sentiment is not None and isinstance(sentiment, str):
            stmt = stmt.where(Article.sentiment == sentiment.lower())

        stmt = stmt.order_by(Article.published_at.desc()).limit(5)

        result = await self._session.execute(stmt)
        articles = result.scalars().all()

        if not articles:
            return f'Статей с упоминанием "{entity}" не найдено.'

        lines = [f'Найдено {len(articles)} статей с упоминанием "{entity}":']
        for art in articles:
            sent_str = art.sentiment or 'unknown'
            lines.append(f'- [{art.id}] {art.title[:60]}... (Тональность: {sent_str})')

        return '\n'.join(lines)


def make_entity_tool(session: AsyncSession) -> SearchByEntityTool:
    """Создаёт инструмент поиска по сущностям."""
    return SearchByEntityTool(session)
