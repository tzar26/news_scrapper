"""Smoke-тест RAG-chain: полный пайплайн на трёх вопросах."""

from __future__ import annotations

import asyncio

from news_scraper.db.session import SessionLocal
from news_scraper.rag.chains import answer_question

QUESTIONS = [
    'Что происходит с нефтью?',
    'Что нового с ключевой ставкой?',
    'Что пишут про автопром Китая?',  # ожидаем fallback
]


async def main() -> None:
    """Прогоняет три вопроса, печатает ответ и источники."""
    async with SessionLocal() as session:
        for question in QUESTIONS:
            print(f'\n{"=" * 70}')
            print(f'ВОПРОС: {question}')
            print('=' * 70)

            result = await answer_question(session, question, top_k=3)

            print(f'\nОТВЕТ:\n{result.answer}')

            if result.sources:
                print(f'\nИСТОЧНИКИ ({len(result.sources)}):')
                for s in result.sources:
                    print(f'  [{s.id}] {s.title[:70]}')
            else:
                print('\n(источники не найдены)')


if __name__ == '__main__':
    asyncio.run(main())
