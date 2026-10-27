# News Scraper & AI Market Analyst

Асинхронный скрапер новостей и аналитическая система на базе локальных LLM для прогнозирования рыночных сигналов.
Проект собирает данные по трем странам (РФ, США, КНР), извлекает структурированные сигналы и позволяет задавать вопросы по базе данных через RAG и LangGraph-агента.

## Ключевые особенности

- **100% локальный инференс**: Никаких облачных API (OpenAI, Anthropic). Все модели (Qwen 2.5, BGE-M3) работают на собственном железе через Ollama (устойчивость к санкциям).
- **Hybrid Search**: Поиск по базе сочетает векторный поиск (pgvector) и полнотекстовый BM25 (PostgreSQL tsvector) с объединением результатов через RRF (Reciprocal Rank Fusion).
- **RAG с цитированием**: Ответы на вопросы опираются только на собранные статьи, с обязательными ссылками на источники.
- **LLM-категоризация**: Автоматическое определение темы статьи (Политика, Экономика, Энергетика и т.д.) с помощью локальной LLM (Qwen 2.5).
- **Агентная аналитика**: LangGraph-агент умеет не только искать статьи, но и отвечать на аналитические вопросы (например, «Сколько статей про энергетику мы собрали за 3 дня?») с помощью инструмента `get_metrics`.
- **Multi-step Agent (LangGraph)**: Агент умеет рассуждать, самостоятельно вызывать инструменты (поиск по базе) и сравнивать факты.
- **Observability**: Полный трейсинг всех шагов LLM (LangGraph, RAG, tool calls) через self-hosted Langfuse.
- **Streaming (SSE)**: Ответы печатаются в реальном времени в UI, агент показывает статусы своей работы («Ищу...», «Анализирую...»).
- **Архитектурная дисциплина**: Изоляция доменной логики от фреймворков (LangChain используется только в слое агентов), документирование всех решений через ADR.
- **NER**: Извлечение компаний, персон и стран с помощью LLM. Агент умеет искать по сущностям (например, «новости про ЦБ»).

## Технологический стек

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), asyncpg
- **База данных**: PostgreSQL 17 + pgvector (векторы + реляционные данные), Redis (кэш, брокер Celery)
- **LLM & AI**: Ollama (Qwen2.5-Coder 14B для генерации, BGE-M3 для эмбеддингов), LangGraph (оркестрация агента), FlashRank / Jina Reranker (опционально)
- **Data Pipeline**: Celery + Celery Beat (фоновый сбор), feedparser, httpx
- **Frontend**: Streamlit (интерактивный дашборд)
- **Observability**: Langfuse (self-hosted)
- **Инфраструктура**: Docker Compose, GitHub Actions (CI)

## [Архитектура проекта](docs/architecture.md)

## Как запустить локально

### Предварительные требования
- Python 3.12
- Docker и Docker Compose
- Запущенный сервер Ollama (локально или удаленно) с моделями `qwen2.5-coder:14b-16k` и `bge-m3`.

### 1. Клонирование и установка
```bash
git clone https://github.com/your-username/news_scruper.git
cd news_scruper
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Настройка окружения
Создайте .env файл на основе .env.example:

```bash env
DATABASE_URL=postgresql+asyncpg://news:news@localhost:5434/pet_news
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434 # или ваш IP
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

### 3. Запуск инфраструктуры
```bash
# Запускает PostgreSQL (с pgvector) и Redis
docker compose up -d postgres redis
```

Можно запустить всё в контейнере и использовать (пропускаем 4-6)
```bash
docker compose up -d
```
Останов в случае контейнерного запуска
```bash
docker compose down
```

### 4. Миграции БД
```bash
alembic upgrade head
```

### 5. Скачивание моделей (если Ollama локально)
```bash
ollama pull qwen2.5-coder:14b-16k
ollama pull bge-m3
```

### 6. Запуск
```bash
# Терминал 1: API
uvicorn news_scraper.api.main:app --reload --port 8000

# Терминал 2: Streamlit Dashboard
streamlit run src/news_scraper/dashboard/app.py

# Терминал 3: Celery Worker (для фонового сбора и эмбеддингов)
celery -A news_scraper.tasks.celery_app:celery_app worker --loglevel=info
```

### Доступ к интерфейсам

Streamlit Dashboard: http://localhost:8501
FastAPI Swagger UI: http://localhost:8000/docs
Langfuse UI: http://localhost:3000 (если запущен)

## Текущий статус и метрики

На данный момент собрано **~5300 статей** из **19 источников**. База данных включает векторные представления (BGE-M3, 1024d) и HNSW-индекс для быстрого поиска.

- **Категоризация**: 100% статей классифицированы LLM (в фоне).
- **Retrieval (Hybrid search)**: `Recall@5` ~ 0.53, `Precision@5` ~ 0.73, `MRR@5` ~ 0.90.
- **Агент**: Поддерживает tool calling (поиск и агрегация метрик), трейсинг через Langfuse.

## Архитектурные решения (ADR)

Все ключевые решения задокументированы в папке docs/decisions/:
- 001 — Изоляция доменной логики.
- 007 — RAG-архитектура (pgvector, BGE-M3).
- 009 — Hybrid Search (BM25 + Vector + RRF).
- 012 — Reranking (Jina Reranker v2 как опциональная фича).
- 013 — LangGraph Agent (State Machine, Tool Calling).

## Планы на будущее (Roadmap)

Проект активно развивается. Ниже представлены задачи, которые запланированы к реализации (в порядке приоритета).

### Сделано
- [x] **LLM-классификация статей по рубрикам (`category_predicted`)**.
- [x] **Инструмент `get_metrics` для LangGraph-агента**.
- [x] **CI/CD (GitHub Actions), Docker Compose, Langfuse (трейсинг)**.
- [x] **NLP Обогащение**: статьи классифицированы и из них извлечены сущности(в фоне).

### В работе (Следующий этап)
- [ ] **Извлечение сущностей (NER)**: Выделение компаний, персон и стран из текста.

### NLP & Обогащение данных
- [ ] **Автоматическая классификация**: LLM-классификация статей по рубрикам (`category_predicted`), взамен неполным данным из RSS.
- [ ] **Извлечение сущностей (NER)**: Выделение компаний, персон и стран из текста новостей.

### Расширение источников (Фокус на РФ)
- [ ] **E-disclosure.ru**: Интеграция через официальное API (не RSS) для получения данных о существенных фактах и отчётности компаний.
- [ ] **Поиск RSS для БКС Экспресс, SmartLab, InvestFuture, Forbes Russia**: Проверка альтернативных путей (Google News RSS по `site:`, скрытые API) или написание HTML-парсеров для этих важных финансовых медиа.

### Улучшение RAG и Агентов
- [ ] **Query Expansion (HyDE)**: Генерация гипотетического ответа перед поиском для повышения полноты (Recall).
- [ ] **Настоящий стриминг токенов**: Проброс нативного `astream` из Ollama в LangGraph для агента.
- [ ] **Оценка генерации (LLM-as-a-judge)**: Внедрение метрик Faithfulness и Answer Relevance с помощью Langfuse.
- [ ] **Ре-тестирование Reranking**: Оценка Jina Reranker v2 при росте корпуса до 10k+ документов.

### UX / UI (Streamlit)
- [ ] **Временные фильтры**: Добавление пресетов «За 1 день», «За 3 дня», «За неделю» на страницы поиска и RAG для анализа краткосрочных трендов.
- [ ] **История диалога**: Сохранение контекста беседы с агентом в рамках одной сессии.

### Инфраструктура и Инженерия
- [ ] **CI/CD**: Настройка GitHub Actions для автоматического запуска `ruff`, `mypy` и `pytest`.
- [ ] **Полная контейнеризация**: Упаковка API, Celery и Streamlit в единый `docker-compose.yml`.
- [ ] **Изоляция тестов (Testcontainers)**.
