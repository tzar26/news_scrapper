news_scruper/
├── README.md
├── requirements.txt
├── pyproject.toml              # ← добавить (современная альтернатива requirements)
├── .clinerules/                # уже есть
├── .continue/                  # ← добавить, если используете Continue
│   └── config.yaml
│
├── src/
│   └── news_scruper/           # ← единый пакет (PEP 8)
│       ├── __init__.py
│       │
│       ├── domain/             # ← чистая логика, НЕ зависит от фреймворков
│       │   ├── __init__.py
│       │   ├── models.py       # Pydantic-модели: NewsItem, SentimentResult
│       │   ├── scraper/        # Scrapy-пауки
│       │   │   ├── __init__.py
│       │   │   ├── spiders/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── reuters.py
│       │   │   │   └── tass.py
│       │   │   ├── items.py
│       │   │   ├── pipelines.py
│       │   │   └── settings.py
│       │   └── nlp/            # sentiment, суммаризация (без LLM-обёрток)
│       │       ├── __init__.py
│       │       └── sentiment.py
│       │
│       ├── agents/             # ← здесь LangChain / LangGraph
│       │   ├── __init__.py
│       │   ├── orchestrator.py # агент-диспетчер
│       │   ├── reviewer.py     # агент-ревьюер кода
│       │   └── tools.py        # @tool-обёртки над domain/
│       │
│       ├── infra/              # ← адаптеры к внешнему миру
│       │   ├── __init__.py
│       │   ├── ollama_client.py    # прямой клиент Ollama
│       │   ├── langfuse_client.py  # self-hosted наблюдаемость
│       │   └── database.py         # SQLite/aiosqlite
│       │
│       └── api/                # ← FastAPI
│           ├── __init__.py
│           ├── main.py
│           ├── routes/
│           │   ├── __init__.py
│           │   └── news.py
│           └── deps.py         # зависимости FastAPI
│
├── tests/
│   ├── __init__.py
│   ├── domain/                 # ← тесты чистой логики, без LLM
│   ├── agents/                 # ← тесты агентов (mock LLM)
│   └── api/                    # ← тесты FastAPI
│
├── data/
│   └── news.db
│
├── scripts/                    # ← утилиты запуска
│   ├── run_scraper.py
│   └── run_api.py
│
└── docker-compose.yml          # ← для Langfuse (self-hosted) и других сервисов