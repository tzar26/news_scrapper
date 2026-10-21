from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.rss import RSSSource


class InvestFutureSource(RSSSource):
    """RSS-источник InvestFuture (Россия)."""

    name = 'investfuture'
    country = Country.RUSSIA
    rss_url = 'https://investfuture.ru/rss/google/producer'
