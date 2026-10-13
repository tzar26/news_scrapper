from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class OilPriceSource(RSSSource):
    """
    RSS-источник OilPrice (Мир).
    """

    name = 'OilPrice'
    country = Country.OTHER
    rss_url = 'https://oilprice.com/rss/main'
