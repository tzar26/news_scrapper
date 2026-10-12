# ADR-008: RAG-пайплайн — retriever, дедупликация, fallback

Дата: 2026-10-12
Статус: принято

## Контекст

Эмбеддинги статей посчитаны (bge-m3, 1024d), HNSW-индекс создан.
Нужен retrieval + генерация ответов с цитированием источников.

Специфика проекта:
- Перепечатки сохранены (cross-source evidence), нужно дедуплицировать
  на этапе retrieval, не ingest.
- Статьи короткие (500–3000 знаков) — один chunk на статью.
- Локальная LLM через Ollama, никаких облачных API.
- LangChain разрешён только в `rag/chains.py` и `agents/`.

## Решения

### 1. Retrieval — SQL через pgvector, без LangChain

`rag/retriever.py::search()` — чистая async-функция:
- embed запроса через OllamaClient,
- SELECT через pgvector (оператор `<=>`),
- фильтры по метаданным (country, category, published_at),
- дедупликация по `content_hash`: top-K **уникальных историй**,
  для каждой — список связанных article_id и url.

LangChain здесь не нужен — это простой SQL. Изоляция по ADR-001.

### 2. Дедупликация на retrieval

pgvector возвращает top-N по близости (N = top_k * 3, с запасом на дубли).
Затем в Python:
- группируем по `content_hash`,
- оставляем одну «представительскую» статью на группу (самую близкую),
- собираем все связанные URL.

Результат: `SearchResult` — dataclass с полями:
- `representative_id`, `representative_url`, `title`, `text`, `distance`,
- `content_hash`,
- `related: list[tuple[int, str]]` — (id, url) перепечаток.

### 3. Промпт — LangChain, но с явными правилами

`rag/prompts.py` — системный промпт:
- Требует цитирования `[article_id]` для каждого утверждения.
- Fallback: если в контексте нет ответа — «не найдено в базе».
- Запрет на использование собственных знаний вне контекста.

`rag/chains.py` — LangChain chain:
- `ChatOllama(model='qwen2.5-coder:14b-16k')`,
- prompt template,
- `|` композиция.

LangChain оправдан: композиция, шаблоны, переиспользование.

### 4. API — `POST /ask`

Request:
```json
{"question": "что влияет на рынок нефти за неделю?", "top_k": 5}
```
Response:
```json
{
  "answer": "...",
  "sources": [
    {"id": 123, "url": "...", "title": "..."},
    {"id": 456, "url": "...", "title": "..."}
  ]
}
```
