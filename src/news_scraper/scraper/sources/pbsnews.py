from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class PBSNewsSource(RSSSource):
    """RSS-источник PBS NewsHour (США)."""

    name = 'PBS NewsHour'
    country = Country.USA
    rss_url = 'https://www.pbs.org/newshour/feeds/rss/headlines'
