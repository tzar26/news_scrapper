from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class CBRFSource(RSSSource):
    """RSS-источник ЦБ РФ (Россия)."""

    name = 'Central bank of Russia'
    country = Country.RUSSIA
    rss_url = 'http://www.cbr.ru/rss/RssPress'
