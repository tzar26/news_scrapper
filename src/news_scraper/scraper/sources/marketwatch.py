from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class MarketWatchSource(RSSSource):
    """
    RSS-источник MarketWatch (США).
    """

    name = 'MarketWatch'
    country = Country.USA
    rss_url = 'https://feeds.content.dowjones.io/public/rss/mw_topstories'
