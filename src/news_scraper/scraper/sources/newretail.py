from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class NewRetailSource(RSSSource):
    """RSS-источник New-Retail.ru (Россия, ритейл)."""

    name = 'new retail'
    country = Country.RUSSIA
    rss_url = 'https://new-retail.ru/rss/'
