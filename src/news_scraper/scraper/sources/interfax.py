from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class InterfaxSource(RSSSource):
    """RSS-источник Интерфакс (Россия)."""

    name = 'interfax'
    country = Country.RUSSIA
    rss_url = 'https://www.interfax.ru/rss'
