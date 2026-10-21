from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class SmartLabSource(RSSSource):
    """RSS-источник SmartLab (Россия)."""

    name = 'smartlab'
    country = Country.RUSSIA
    rss_url = 'https://smart-lab.ru/rss/flow/'
