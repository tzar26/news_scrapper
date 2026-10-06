from __future__ import annotations

import httpx

from news_scraper.domain.enums import Category, Country
from news_scraper.domain.models import RawNewsItem
from news_scraper.scraper.parsers import parse_rss


class RSSSource:
    """
    Base class for RSS sources.
    """

    name: str
    country: Country
    rss_url: str
    default_category: Category = Category.OTHER

    def __init__(self, client: httpx.AsyncClient | None = None):
        """
        Initializes the RSSSource.

        :param client: An optional httpx.AsyncClient instance. If None, a new client will be created.
        """
        if client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        else:
            self._client = client
        self._owns_client = client is None

    async def fetch(self) -> list[RawNewsItem]:
        """
        Fetches news items from the RSS feed.

        :return: A list of RawNewsItem instances.
        """
        async with self._client as client:
            response = await client.get(self.rss_url)
            response.raise_for_status()
            return parse_rss(
                response.content,
                source_name=self.name,
                country=self.country,
                default_category=self.default_category,
            )

    async def aclose(self) -> None:
        """
        Closes the client if it was created by this instance.
        """
        if hasattr(self, '_client'):
            await self._client.aclose()
