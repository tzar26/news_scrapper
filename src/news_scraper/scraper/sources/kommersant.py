from __future__ import annotations

from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource

RSS_URL = 'https://www.kommersant.ru/rss/news.xml'


class KommersantSource(RSSSource):
    """
    RSS-источник «Коммерсант».
    """

    name = 'kommersant'
    country = Country.RUSSIA
    rss_url = RSS_URL
