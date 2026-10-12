from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class TASSSource(RSSSource):
    """
    RSS-источник ТАСС (Россия).
    """

    name = 'TASS'
    country = Country.RUSSIA
    rss_url = 'https://tass.ru/rss/v2.xml'
