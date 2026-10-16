"""Smoke-тест reranker: сравнение порядка до/после."""

from __future__ import annotations

import asyncio

from news_scraper.db.session import SessionLocal
from news_scraper.rag.reranker import Reranker
from news_scraper.rag.retriever import search


async def main() -> None:
    """Прогоняет запрос, показывает top-10 до и после reranking."""
    query = 'экспорт российского газа'

    async with SessionLocal() as session:
        # Берём top-20 кандидатов
        results = await search(session, query, top_k=20)

        print(f'=== ДО reranking (top-10 из {len(results)}) ===')
        for i, r in enumerate(results[:10], 1):
            print(f'{i:2}. [{r.rrf_score:.4f}] {r.title[:70]}')

        reranker = Reranker(model_name='jinaai/jina-reranker-v2-base-multilingual')
        reranked = reranker.rerank(query, results, top_k=10)

        print('\n=== ПОСЛЕ reranking ===')
        for i, r in enumerate(reranked, 1):
            print(f'{i:2}. {r.title[:70]}')


if __name__ == '__main__':
    asyncio.run(main())
