from __future__ import annotations

from datetime import UTC, datetime

import feedparser
from pydantic import ValidationError

from news_scraper.domain.enums import Category, Country
from news_scraper.domain.models import RawNewsItem

_CATEGORY_MAP: dict[str, Category] = {
    'политика': Category.POLITICS,
    'politics': Category.POLITICS,
    'экономика': Category.ECONOMY,
    'economy': Category.ECONOMY,
    'бизнес': Category.BUSINESS,
    'business': Category.BUSINESS,
    'технологии': Category.TECHNOLOGY,
    'technology': Category.TECHNOLOGY,
    # добавляй по мере необходимости
}


def _map_category(raw: str | None, default: Category) -> Category:
    """Приводит категорию из RSS к нашему enum."""
    if not raw:
        return default
    return _CATEGORY_MAP.get(raw.strip().lower(), default)


def parse_rss(
    content: bytes,
    *,
    source_name: str,
    country: Country,
    default_category: Category = Category.OTHER,
) -> list[RawNewsItem]:
    """
    Parses an RSS feed and returns a list of RawNewsItem objects.

    Args:
        content (bytes): The RSS feed content.
        source_name (str): The name of the source.
        country (Country): The country of the source.
        default_category (Category, optional): The default category for the news items. Defaults to Category.OTHER.

    Returns:
        list[RawNewsItem]: A list of RawNewsItem objects.
    """
    feed = feedparser.parse(content)
    news_items = []
    skipped = 0

    for entry in feed.entries:
        if 'published_parsed' not in entry:
            continue

        published_at = datetime(*entry.published_parsed[:6], tzinfo=UTC)
        url = entry.link
        title = entry.title
        text = entry.get('summary', '')
        category = _map_category(entry.get('category'), default_category)

        try:
            news_item = RawNewsItem(
                source=source_name,
                country=country,
                category=category,
                published_at=published_at,
                url=url,
                title=title,
                text=text,
            )
            news_items.append(news_item)
        except ValidationError as e:
            print(f'[parse_rss] validation failed for {url}: {e.errors()}')
            skipped += 1
            continue

    return news_items
