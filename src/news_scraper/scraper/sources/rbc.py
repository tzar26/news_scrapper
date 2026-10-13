from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class RBCSource(RSSSource):
    """RSS-источник RBC (Россия)."""

    name = 'RBC'
    country = Country.RUSSIA
    rss_url = 'https://rssexport.rbc.ru/rbcnews/news/30/full.rss'
