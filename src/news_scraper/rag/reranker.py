"""Reranker: cross-encoder на sentence-transformers для пересортировки результатов."""

from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import CrossEncoder

from news_scraper.rag.retriever import SearchResult

logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'jinaai/jina-reranker-v2-base-multilingual'


@lru_cache(maxsize=1)
def _get_model(model_name: str = DEFAULT_MODEL) -> CrossEncoder:
    """Ленивая инициализация CrossEncoder (модель грузится один раз).

    trust_remote_code=True нужен для Jina Reranker v2 — модель
    использует кастомный код.
    """
    logger.info('loading cross-encoder: %s', model_name)
    return CrossEncoder(model_name, trust_remote_code=True)


class Reranker:
    """Обёртка над sentence-transformers CrossEncoder.

    Cross-encoder получает пары (query, document) и выдаёт оценки
    релевантности точнее, чем bi-encoder (embedding + cosine).
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        """Инициализация. Модель грузится лениво при первом вызове."""
        self._model_name = model_name

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Пересортировывает результаты и возвращает top_k.

        Args:
            query: поисковый запрос.
            results: результаты retrieval (top-30..50).
            top_k: сколько оставить после reranking.

        Returns:
            SearchResult, отсортированные по cross-encoder score.
        """
        if not results:
            return []

        model = _get_model(self._model_name)

        pairs = [(query, f'{r.title}\n\n{r.text[:1500]}') for r in results]
        scores = model.predict(pairs)

        ranked = sorted(
            zip(results, scores),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return [r for r, _ in ranked[:top_k]]
