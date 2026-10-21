from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class VedomostiSource(RSSSource):
    """RSS-источник Ведомости (Россия)."""

    name = 'vedomosti'
    country = Country.RUSSIA
    rss_url = 'https://www.vedomosti.ru/rss/news'
