from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class XinhuaSource(RSSSource):
    """
    RSS-источник Xinhua (Китай).
    """

    name = 'Xinhua'
    country = Country.CHINA
    rss_url = 'http://www.xinhuanet.com/english/rss/worldrss.xml'
