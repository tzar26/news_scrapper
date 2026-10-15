"""Оценка retrieval-метрик на размеченном test set."""

from __future__ import annotations

from pathlib import Path

import yaml

CANDIDATES_PATH = Path('tests/rag/candidates.yaml')
BASELINE_PATH = Path('tests/rag/baseline.txt')
KS = [1, 3, 5]


def evaluate_query(candidates: list[dict], ks: list[int]) -> dict[str, float]:
    """Считает метрики для одного запроса.

    Args:
        candidates: список кандидатов, отсортированный по релевантности.
        ks: значения k для recall@k, precision@k.

    Returns:
        Dict с метриками. Пустой, если нет релевантных.
    """
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


def main() -> None:
    """Прогоняет все запросы, печатает сводку и сохраняет baseline."""
    with CANDIDATES_PATH.open() as f:
        data = yaml.safe_load(f)

    queries = data['queries']

    # Собираем все метрики по всем запросам
    all_values: dict[str, list[float]] = {}
    per_query: list[tuple[str, dict[str, float]]] = []

    for q in queries:
        metrics = evaluate_query(q['candidates'], KS)
        if not metrics:
            per_query.append((q['query'], {}))
            continue
        per_query.append((q['query'], metrics))
        for key, value in metrics.items():
            all_values.setdefault(key, []).append(value)

    # Усредняем
    avg_metrics = {k: sum(v) / len(v) for k, v in all_values.items()}

    # Печать сводки
    n_effective = len(all_values.get('recall@5', []))
    print(f'=== Retrieval Metrics ({n_effective} queries with relevant) ===')
    for key in sorted(avg_metrics):
        print(f'{key:<15} {avg_metrics[key]:.4f}')

    # Печать по запросам
    print('\n=== Per-query ===')
    print(f'{"query":<35} {"recall@5":>10} {"precision@5":>12} {"mrr@5":>8}')
    for query_text, metrics in per_query:
        if not metrics:
            print(f'{query_text:<35} {"(no relevant)":>30}')
            continue
        print(
            f'{query_text:<35} '
            f'{metrics["recall@5"]:>10.4f} '
            f'{metrics["precision@5"]:>12.4f} '
            f'{metrics["mrr@5"]:>8.4f}'
        )

    # Сохранение baseline
    with BASELINE_PATH.open('w') as f:
        for key in sorted(avg_metrics):
            f.write(f'{key} {avg_metrics[key]:.4f}\n')

    print(f'\nBaseline сохранён в {BASELINE_PATH}')


if __name__ == '__main__':
    main()
