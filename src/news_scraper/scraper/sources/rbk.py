from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class RBKSource(RSSSource):
    """RSS-источник РБК (Россия)."""

    name = 'RBK'
    country = Country.RUSSIA
    rss_url = 'https://rssexport.rbc.ru/rbcnews/news/30/full.rss'
