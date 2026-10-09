from __future__ import annotations

import redis

from news_scraper.infra.settings import settings

# Модульная переменная
_redis_client: redis.Redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)


# Функции
def acquire_lock(key: str, ttl_seconds: int) -> bool:
    """Пытается захватить распределённую блокировку.
    SET key 1 NX EX ttl — атомарная операция.
    Возвращает True если блокировка захвачена, False если уже занята.
    """
    return bool(_redis_client.set(key, '1', nx=True, ex=ttl_seconds))


def release_lock(key: str) -> None:
    """Освобождает блокировку (удаляет ключ). Идемпотентно."""
    _redis_client.delete(key)
