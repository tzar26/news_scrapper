"""Настройки приложения через pydantic-settings."""

from __future__ import annotations

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    database_url: str = Field(description='DSN для PostgreSQL')
    redis_url: str = Field(default='redis://localhost:6379/0', description='DSN для Redis')
    ollama_base_url: str = Field(default='http://localhost:11434', description='URL Ollama')
    log_level: str = Field(default='INFO', description='Уровень логирования')
    celery_broker_url: str = Field(
        default='redis://localhost:6379/1', description='DSN брокера Celery'
    )
    celery_result_backend: str = Field(
        default='redis://localhost:6379/2', description='DSN backend результатов Celery'
    )

    langfuse_public_key: str | None = Field(default=None, description='Langfuse public key')
    langfuse_secret_key: str | None = Field(default=None, description='Langfuse secret key')
    langfuse_host: str = Field(default='http://localhost:3000', description='Langfuse host')


settings = Settings()

# Langfuse SDK читает ключи напрямую из os.environ.
# Pydantic-settings не экспортирует их автоматически.
if settings.langfuse_public_key:
    os.environ['LANGFUSE_PUBLIC_KEY'] = settings.langfuse_public_key
if settings.langfuse_secret_key:
    os.environ['LANGFUSE_SECRET_KEY'] = settings.langfuse_secret_key
os.environ['LANGFUSE_HOST'] = settings.langfuse_host
