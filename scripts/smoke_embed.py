"""Smoke-тест: получить эмбеддинг одной фразы через Ollama."""

from __future__ import annotations

import asyncio

from news_scraper.infra.ollama_client import OllamaClient


async def main() -> None:
    """Считает эмбеддинг двух фраз, печатает dim и cosine similarity."""
    client = OllamaClient()
    try:
        vec_a = await client.embed('ключевая ставка ЦБ РФ выросла', model='bge-m3')
        vec_b = await client.embed('Центробанк повысил ключевую ставку', model='bge-m3')
        vec_c = await client.embed('в Москве открыли новый парк', model='bge-m3')

        print(f'dim: {len(vec_a)}')

        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(x * x for x in b) ** 0.5
            return dot / (na * nb) if na and nb else 0.0

        print(f'close topics:  {cosine(vec_a, vec_b):.3f}')
        print(f'different:     {cosine(vec_a, vec_c):.3f}')
    finally:
        await client.aclose()


if __name__ == '__main__':
    asyncio.run(main())
