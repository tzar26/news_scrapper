from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class ForbesRssAppSource(RSSSource):
    """RSS-источник Forbes Russia через rss.app (сторонний прокси)."""

    name = 'forbes_rssapp'
    country = Country.RUSSIA
    rss_url = 'https://rss.app/feeds/fa0qDEpp6vW0nFis.xml'
