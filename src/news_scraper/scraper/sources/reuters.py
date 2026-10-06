from __future__ import annotations

import httpx

from news_scraper.domain.enums import Country
from news_scraper.domain.models import RawNewsItem
from news_scraper.scraper.parsers import parse_rss
from news_scraper.scraper.sources.base import Source

RSS_URL = 'https://www.reuters.com/arc/outboundfeeds/rss/'


class ReutersSource(Source):
    """
    Reuters news source.
    """

    name = 'reuters'
    country = Country.USA

    def __init__(self, client: httpx.AsyncClient | None = None):
        """
        Initialize the source with an optional client.
        If no client is provided, create a new one with a timeout of 10 seconds.
        """
        if client is None:
            self._client = httpx.AsyncClient(timeout=10)
        else:
            self._client = client

    async def fetch(self) -> list[RawNewsItem]:
        """
        Fetch news items from the source.
        """
        async with self._client as client:
            response = await client.get(RSS_URL)
            response.raise_for_status()
            return parse_rss(response.content, source_name=self.name, country=self.country)

    async def aclose(self):
        """
        Close the client if it was created inside.
        """
        if hasattr(self, '_client'):
            await self._client.aclose()
