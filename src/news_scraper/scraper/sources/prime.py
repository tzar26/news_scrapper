from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class PrimeSource(RSSSource):
    """
    RSS-источник Prime (Россия).
    """

    name = 'Prime'
    country = Country.RUSSIA
    rss_url = 'https://1prime.ru/export/rss2/index.xml'
