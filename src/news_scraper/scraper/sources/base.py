from __future__ import annotations

from typing import Protocol

from news_scraper.domain.enums import Country
from news_scraper.domain.models import RawNewsItem


class Source(Protocol):
    """
    Protocol for a news source.
    """

    name: str
    """
    Short name of the source (e.g. "kommersant").
    """

    country: Country
    """
    Country of the source.
    """

    async def fetch(self) -> list[RawNewsItem]:
        """
        Fetch the latest news items from the source.

        Returns:
            list[RawNewsItem]: List of raw news items.
        """
