"""Скрипт для ручной валидации качества NLP-разметки (Data-Centric AI)."""

from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from news_scraper.db.models import Article
from news_scraper.db.session import SessionLocal


async def main() -> None:
    """Выбирает 20 случайных статей и выводит их для проверки."""
    async with SessionLocal() as session:
        # Выбираем случайные статьи, где есть и категория, и тональность
        stmt = (
            select(Article)
            .where(Article.category_predicted.is_not(None))
            .where(Article.sentiment.is_not(None))
            .order_by(func.random())
            .limit(20)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

        print(f'=== ВАЛИДАЦИЯ ВЫБОРКИ ({len(articles)} статей) ===\n')

        for i, art in enumerate(articles, 1):
            print(f'[{i}] {art.title}')
            print(f'    URL: {art.url}')
            print(f'    LLM Категория: {art.category_predicted}')
            print(f'    LLM Тональность: {art.sentiment}')
            print(f'    Текст (первые 300 символов): {art.text[:300].strip()}...')
            print('-' * 80)


if __name__ == '__main__':
    asyncio.run(main())
