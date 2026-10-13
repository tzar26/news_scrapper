from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.base import Source
from news_scraper.scraper.sources.cnbc import CNBCSource
from news_scraper.scraper.sources.gtchina import GTChinaSource
from news_scraper.scraper.sources.interfax import InterfaxSource
from news_scraper.scraper.sources.kommersant import KommersantSource
from news_scraper.scraper.sources.marketwatch import MarketWatchSource
from news_scraper.scraper.sources.npr import NPRSource
from news_scraper.scraper.sources.nyt import NYTSource
from news_scraper.scraper.sources.oilprice import OilPriceSource
from news_scraper.scraper.sources.prime import PrimeSource
from news_scraper.scraper.sources.rbc import RBCSource
from news_scraper.scraper.sources.rbk import RBKSource
from news_scraper.scraper.sources.tass import TASSSource
from news_scraper.scraper.sources.wsj import WSJSource
from news_scraper.scraper.sources.xinhua import XinhuaSource

ALL_SOURCES: list[type[Source]] = [
    KommersantSource,
    NPRSource,
    RBKSource,
    TASSSource,
    WSJSource,
    XinhuaSource,
    GTChinaSource,
    InterfaxSource,
    PrimeSource,
    OilPriceSource,
    CNBCSource,
    MarketWatchSource,
    RBCSource,
    NYTSource,
]


def get_sources_by_country(country: Country) -> list[type[Source]]:
    """Возвращает классы источников для указанной страны."""
    return [s for s in ALL_SOURCES if s.country == country]


# TODO: добавить источники
# США:
#   - PBS NewsHour (https://www.pbs.org/newshour/feeds/rss/headlines)
#   - Politico (https://rss.politico.com/politics-news.xml)
#   - NYT (https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml)
# После добавления — не забыть экспортировать в __init__.py
# и добавить класс в ALL_SOURCES.
