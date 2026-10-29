"""Тест Market Impact v2."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from news_scraper.db.models import Article
from news_scraper.db.session import SessionLocal
from news_scraper.nlp.market_impact import extract_market_impact


async def main() -> None:
    """Берет 10 свежих статей и показывает их Impact."""
    async with SessionLocal() as session:
        stmt = (
            select(Article)
            .where(Article.category_predicted.is_not(None))
            .order_by(Article.published_at.desc())
            .limit(25)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

        print(f'=== ТЕСТ MARKET IMPACT v2 ({len(articles)} статей) ===\n')

        for art in articles:
            print(f'Заголовок: {art.title}...')
            print(f'Text: {art.text}...')
            print(f'LLM Категория: {art.category_predicted}')

            impact = await extract_market_impact(art.title, art.text)

            if not impact:
                print('  (Ошибка)')
            else:
                print(f'  Тип: {impact.get("type")}')
                print(f'  Масштаб: {impact.get("importance").upper()}')
                print(f'  Рынок: {impact.get("target_market")}')
                print(f'  Сектор: {impact.get("main_sector")} -> {impact.get("direction").upper()}')

            print('-' * 80)


if __name__ == '__main__':
    asyncio.run(main())
