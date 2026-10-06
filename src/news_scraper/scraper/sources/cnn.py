from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class CNNSource(RSSSource):
    """
    RSS-источник CNN (США).
    """

    name = 'cnn'
    country = Country.USA
    rss_url = 'http://rss.cnn.com/rss/cnn_topstories.rss'
