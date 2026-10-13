from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class NYTSource(RSSSource):
    """RSS-источник NYT (США)."""

    name = 'NYT'
    country = Country.USA
    rss_url = 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml'
