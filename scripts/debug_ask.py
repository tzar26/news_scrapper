"""Debug: вызывает answer_question напрямую, минуя API."""

from __future__ import annotations

import asyncio
import time

from news_scraper.db.session import SessionLocal
from news_scraper.rag.chains import answer_question


async def main() -> None:
    """Проверяет полный RAG-пайплайн на одном вопросе."""
    async with SessionLocal() as session:
        start = time.monotonic()
        result = await answer_question(session, 'Что нового с ключевой ставкой ЦБ?', top_k=3)
        elapsed = time.monotonic() - start

        print(f'=== elapsed: {elapsed:.1f}s ===')
        print(f'\nresults (retrieval hits): {len(result.results)}')
        for r in result.results:
            print(f'  [{r.rrf_score:.4f}] {r.title[:70]}')

        print(f'\nanswer ({len(result.answer)} chars):')
        print(result.answer)

        print(f'\nsources: {len(result.sources)}')


if __name__ == '__main__':
    asyncio.run(main())
