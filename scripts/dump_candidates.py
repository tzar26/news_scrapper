"""Дамп top-20 кандидатов с переносом старой разметки по ID.

Запуск:
    python -m scripts.dump_candidates

Логика:
- Читает queries.yaml (список запросов).
- Читает существующий candidates.yaml (если есть) и строит map id -> relevant.
- Для каждого запроса делает search top-N.
- Для новых кандидатов — если id есть в старой разметке, переносит метку.
- Если старая разметка содержала релевантные ID, выпавшие из нового top-N,
  они добавляются в конец секции с source='previous_annotation'.
  Это нужно, чтобы recall@k считался корректно (не завышался).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import yaml

from news_scraper.db.session import SessionLocal
from news_scraper.rag.retriever import search

QUERIES_PATH = Path('tests/rag/queries.yaml')
CANDIDATES_PATH = Path('tests/rag/candidates.yaml')
TOP_N = 20


def load_previous_labels() -> dict[str, dict[int, bool]]:
    """Загружает старую разметку из candidates.yaml.

    Returns:
        Dict: query -> {id: relevant}. Пустой, если файла нет.
    """
    if not CANDIDATES_PATH.exists():
        return {}
    with CANDIDATES_PATH.open() as f:
        data = yaml.safe_load(f)
    labels: dict[str, dict[int, bool]] = {}
    for q in data.get('queries', []):
        query = q['query']
        labels[query] = {
            c['id']: c['relevant'] for c in q.get('candidates', []) if c.get('relevant') is not None
        }
    return labels


async def dump_one(
    session,
    query: str,
    previous: dict[int, bool],
) -> tuple[list[dict], list[dict]]:
    """Возвращает (новые_кандидаты, выпавшие_релевантные).

    new_candidates: top-N из search, с перенесёнными метками.
    dropped: ранее релевантные ID, которых нет в top-N.
    """
    results = await search(session, query, top_k=TOP_N)

    new_ids: set[int] = set()
    new_candidates: list[dict] = []
    for r in results:
        rid = r.representative_id
        new_ids.add(rid)
        new_candidates.append(
            {
                'id': rid,
                'source': r.representative_url.split('/')[2] if r.representative_url else '',
                'title': r.title,
                'rrf_score': round(r.rrf_score, 5),
                'relevant': previous.get(rid),  # перенос метки или None
            }
        )

    # Релевантные из прошлого прогона, которых нет в новом top-N
    dropped: list[dict] = []
    for old_id, old_label in previous.items():
        if old_label is True and old_id not in new_ids:
            dropped.append(
                {
                    'id': old_id,
                    'source': 'previous_annotation',
                    'title': '[Выпала из top-N, но размечена релевантной ранее]',
                    'rrf_score': None,
                    'relevant': True,
                }
            )

    return new_candidates, dropped


async def main() -> None:
    """Прогон по всем запросам, сохранение candidates.yaml."""
    with QUERIES_PATH.open() as f:
        queries = yaml.safe_load(f).get('queries', [])

    previous = load_previous_labels()
    print(f'Загружено запросов: {len(queries)}')
    print(f'Найдено старых разметок: {len(previous)}')
    print()

    output: dict = {'queries': []}
    async with SessionLocal() as session:
        for entry in queries:
            query = entry['query']
            prev_for_query = previous.get(query, {})
            print(f'  {query} (было размечено: {len(prev_for_query)} id)')

            new_candidates, dropped = await dump_one(session, query, prev_for_query)
            output['queries'].append(
                {
                    'query': query,
                    'candidates': new_candidates + dropped,
                }
            )

            if dropped:
                print(f'    → выпало из top-{TOP_N}: {len(dropped)} релевантных')

    with CANDIDATES_PATH.open('w') as f:
        yaml.safe_dump(output, f, allow_unicode=True, sort_keys=False)

    print(f'\nГотово: {CANDIDATES_PATH}')
    print('Проверь новые id с relevant: null и проставь метки.')


if __name__ == '__main__':
    asyncio.run(main())
