from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class CNBCSource(RSSSource):
    """RSS-источник CNBC (США)."""

    name = 'CNBC'
    country = Country.USA
    rss_url = 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114'
