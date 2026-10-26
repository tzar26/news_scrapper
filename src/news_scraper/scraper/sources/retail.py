from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class RetailSource(RSSSource):
    """RSS-источник Retail.ru (Россия, ритейл)."""

    name = 'retail'
    country = Country.RUSSIA
    rss_url = 'https://www.retail.ru/rss/news/'
