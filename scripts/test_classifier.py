"""Smoke-тест классификатора на реальных статьях из БД."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from news_scraper.db.models import Article
from news_scraper.db.session import SessionLocal
from news_scraper.nlp.classifier import classify_article


async def main() -> None:
    """Берет 5 случайных статей, классифицирует, выводит результат."""
    async with SessionLocal() as session:
        # Берем 5 свежих статей без предсказанной категории
        stmt = (
            select(Article)
            .where(Article.category_predicted.is_(None))
            .order_by(Article.published_at.desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

        for art in articles:
            category = await classify_article(art.title, art.text)
            print(
                f'Category: {category.value:<12} | Raw: {art.category_raw or "None":<10} | Title: {art.title[:60]}...'
            )


if __name__ == '__main__':
    asyncio.run(main())
