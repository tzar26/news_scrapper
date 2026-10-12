from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class GTChinaSource(RSSSource):
    """
    RSS-источник GlobalTimes (Китай).
    """

    name = 'GlobalTimes China'
    country = Country.CHINA
    rss_url = 'https://www.globaltimes.cn/rss/outbrain.xml'
