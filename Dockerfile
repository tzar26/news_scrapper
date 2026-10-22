FROM python:3.12-slim AS base

# Устанавливаем системные зависимости (нужны для asyncpg, psycopg и сборки некоторых пакетов)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Отключаем создание .pyc файлов и включаем небуферизованный вывод в консоль
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем только файлы, необходимые для установки зависимостей, чтобы использовать кэш Docker
COPY pyproject.toml ./
COPY src/ ./src/
COPY alembic.ini ./
COPY tests/ ./tests/

# Устанавливаем зависимости. Поскольку исходников еще нет, pip установит только пакеты.
# Используем --no-cache-dir для уменьшения размера образа.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]"

# Указываем переменную окружения для Python, чтобы он видел наш пакет
ENV PYTHONPATH=/app/src

# Команда по умолчанию (будет переопределена в docker-compose для разных сервисов)
CMD ["uvicorn", "news_scraper.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
