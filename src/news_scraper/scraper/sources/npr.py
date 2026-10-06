from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class NPRSource(RSSSource):
    """
    RSS-источник NPR (США).
    """

    name = 'npr'
    country = Country.USA
    rss_url = 'https://feeds.npr.org/1001/rss.xml'
