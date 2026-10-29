"""Скрипт для ручной валидации качества категоризации (Data-Centric AI)."""

from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from news_scraper.db.models import Article
from news_scraper.db.session import SessionLocal


async def main() -> None:
    """Выбирает 20 случайных статей с категориями и выводит их для проверки."""
    async with SessionLocal() as session:
        # Выбираем случайные статьи, где категория уже предсказана
        stmt = (
            select(Article)
            .where(Article.category_predicted.is_not(None))
            .order_by(func.random())
            .limit(20)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

        print(f'=== ВАЛИДАЦИЯ КАТЕГОРИЙ ({len(articles)} статей) ===\n')

        for i, art in enumerate(articles, 1):
            print(f'[{i}] {art.title}')
            print(f'    LLM Категория: {art.category_predicted}')
            # Убираем HTML-теги для читаемости (на всякий случай)
            clean_text = art.text.replace('<br />', ' ').replace('<p>', ' ').replace('</p>', ' ')
            print(f'    Текст: {clean_text.strip()}...')
            print('-' * 80)


if __name__ == '__main__':
    asyncio.run(main())
