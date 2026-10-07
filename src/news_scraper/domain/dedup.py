from __future__ import annotations

import hashlib
import re

from news_scraper.domain.models import RawNewsItem


def _normalize(text: str) -> str:
    """
    Нормализует текст для хэширования.
    """
    return re.sub(r'\s+', ' ', text.lower()).strip()


def content_hash(item: RawNewsItem) -> str:
    """
    Возвращает SHA-256 хэш нормализованного title+text.
    """
    normalized_title = _normalize(item.title)
    normalized_text = _normalize(item.text)
    payload = f'{normalized_title}\n{normalized_text}'
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()
