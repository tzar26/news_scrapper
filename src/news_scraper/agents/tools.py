"""Tools для LangGraph-агента."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from news_scraper.rag.retriever import search


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
        query = args.get('query', '')
        if not query:
            return json.dumps({'error': 'query is empty'})

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
