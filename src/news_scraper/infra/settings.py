from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )
    database_url: str = Field(
        description='DSN для PostgreSQL, например postgresql+asyncpg://user:pass@localhost:5432/news'
    )
    redis_url: str = Field(
        default='redis://localhost:6379/0',
        description='DSN для Redis (брокер Celery)',
    )
    ollama_base_url: str = Field(default='http://localhost:11434', description='URL Ollama')
    log_level: str = Field(default='INFO', description='Уровень логирования')
    celery_broker_url: str = Field(
        default='redis://localhost:6379/1',
        description='DSN брокера Celery (Redis, отдельная БД от основного redis_url)',
    )
    celery_result_backend: str = Field(
        default='redis://localhost:6379/2',
        description='DSN backend результатов Celery (Redis)',
    )


settings = Settings()
