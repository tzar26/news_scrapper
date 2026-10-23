"""Smoke-тест извлечения сущностей и тональности."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from news_scraper.db.models import Article
from news_scraper.db.session import SessionLocal
from news_scraper.nlp.extractor import extract_info


async def main() -> None:
    """Берет 3 случайные статьи и прогоняет через LLM."""
    async with SessionLocal() as session:
        stmt = (
            select(Article)
            .where(Article.sentiment.is_(None))
            .order_by(Article.published_at.desc())
            .limit(3)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

        for art in articles:
            print(f'\n--- {art.title[:60]}... ---')
            sentiment, entities = await extract_info(art.title, art.text)

            print(f'Sentiment: {sentiment.value}')
            print('Entities:')
            for ent in entities:
                print(f'  - {ent["text"]} ({ent["type"]})')


if __name__ == '__main__':
    asyncio.run(main())
