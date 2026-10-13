# ADR-009: Hybrid search — BM25 + vector через RRF

Дата: 2026-10-13
Статус: принято

## Контекст

Эмпирика из ADR-008 показала потолок чистого vector search:
- «ключевая ставка ЦБ» → 1/5 релевантных
- «автопром Китая» → 1/5
- «золото» → 1/5
- «нефть ОПЕК» → 5/5

Причины разные: общие термины, омонимия, составные запросы.
Чистый vector не различает точные термины и семантику слов.

## Решение

Hybrid search: **BM25 через PostgreSQL tsvector + vector через pgvector**,
объединение через **RRF (Reciprocal Rank Fusion)**.

### 1. BM25 через функциональные индексы

Не добавляем `tsv`-столбцы в схему. Используем **функциональные GIN-индексы**:

```sql
CREATE INDEX ix_articles_tsv_ru ON articles
USING gin (to_tsvector('russian', title || ' ' || text));

CREATE INDEX ix_articles_tsv_en ON articles
USING gin (to_tsvector('english', title || ' ' || text));
