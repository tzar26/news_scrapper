"""Оценка retrieval-метрик С использованием HyDE."""

from __future__ import annotations

import asyncio
from pathlib import Path

import yaml

from news_scraper.db.session import SessionLocal
from news_scraper.rag.retriever import search

CANDIDATES_PATH = Path('tests/rag/queries.yaml')
KS = [1, 3, 5]


def evaluate_query(candidates: list[dict], ks: list[int]) -> dict[str, float]:
    """Считает метрики для одного запроса (копия из eval_retrieval)."""
    relevant_ids = [c['id'] for c in candidates if c.get('relevant') is True]
    if not relevant_ids:
        return {}
    ranks = [i + 1 for i, c in enumerate(candidates) if c.get('relevant') is True]
    metrics: dict[str, float] = {}
    for k in ks:
        top_k_ids = {c['id'] for c in candidates[:k] if c.get('relevant') is True}
        hits_at_k = len(top_k_ids)
        metrics[f'recall@{k}'] = hits_at_k / len(relevant_ids)
        metrics[f'precision@{k}'] = hits_at_k / k
        first_hit_rank = next((r for r in ranks if r <= k), None)
        metrics[f'mrr@{k}'] = (1.0 / first_hit_rank) if first_hit_rank else 0.0
    return metrics


async def main() -> None:
    """Прогоняет запросы с HyDE и считает метрики."""
    with Path('tests/rag/candidates.yaml').open() as f:
        annotated = yaml.safe_load(f)

    labels_by_query = {
        q['query']: {
            c['id']: c['relevant'] for c in q['candidates'] if c.get('relevant') is not None
        }
        for q in annotated['queries']
    }

    with Path('tests/rag/queries.yaml').open() as f:
        queries_data = yaml.safe_load(f)

    all_metrics: dict[str, list[float]] = {}

    async with SessionLocal() as session:
        for entry in queries_data['queries']:
            query = entry['query']
            labels = labels_by_query.get(query, {})
            if not any(v is True for v in labels.values()):
                continue

            print(f'Processing: {query}...')
            results = await search(session, query, top_k=20, use_hyde=True)

            candidates_with_labels = [
                {'id': r.representative_id, 'relevant': labels.get(r.representative_id, False)}
                for r in results
            ]

            metrics = evaluate_query(candidates_with_labels, KS)
            for k, v in metrics.items():
                all_metrics.setdefault(k, []).append(v)

    avg = {k: sum(v) / len(v) for k, v in all_metrics.items()}
    print('\n=== Retrieval Metrics WITH HyDE ===')
    for k in sorted(avg):
        print(f'{k:<15} {avg[k]:.4f}')


if __name__ == '__main__':
    asyncio.run(main())
