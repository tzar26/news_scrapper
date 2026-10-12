from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class WSJSource(RSSSource):
    """RSS-источник The Wall Street Journal (США)."""

    name = 'wsj'
    country = Country.USA
    rss_url = 'https://feeds.content.dowjones.io/public/rss/RSSUSnews'
