from __future__ import annotations

import httpx

from news_scraper.infra.settings import settings


class OllamaClient:
    """Асинхронный клиент к Ollama (embed и chat)."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        self._base_url = (base_url or settings.ollama_base_url).rstrip('/')
        self._client = httpx.AsyncClient(timeout=timeout)

    async def embed(self, text: str, *, model: str = 'nomic-embed-text') -> list[float]:
        """Возвращает эмбеддинг текста (список float).
        Args:
            text: текст для эмбеддинга. Если пустой — вернётся
            нулевой вектор длины 768.
            model: имя модели в Ollama.
        Raises:
            httpx.HTTPError: при сетевых ошибках или не-2xx ответе.
            ValueError: если ответ не содержит embeddings или их длина != 768.
        """
        if not text.strip():
            return [0.0] * 768

        response = await self._client.post(
            f'{self._base_url}/api/embed',
            json={'model': model, 'input': text},
        )
        response.raise_for_status()
        data = response.json()
        emb = data.get('embeddings', [])[0]
        if not emb:
            raise ValueError('No embeddings found in response')
        if len(emb) != 768:
            raise ValueError(f'Expected 768 dims, got {len(emb)}')
        return list(emb)

    async def aclose(self) -> None:
        """Закрывает клиент."""
        await self._client.aclose()
