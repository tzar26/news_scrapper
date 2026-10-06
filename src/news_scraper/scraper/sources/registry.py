from news_scraper.domain.enums import Country
from news_scraper.scraper.sources.base import Source
from news_scraper.scraper.sources.cnn import CNNSource
from news_scraper.scraper.sources.kommersant import KommersantSource
from news_scraper.scraper.sources.npr import NPRSource

ALL_SOURCES: list[type[Source]] = [
    KommersantSource,
    NPRSource,
    CNNSource,
]


def get_sources_by_country(country: Country) -> list[type[Source]]:
    """Возвращает классы источников для указанной страны."""
    return [s for s in ALL_SOURCES if s.country == country]


# TODO: добавить источники
# Россия:
#   - TASS (https://tass.ru/rss/v2.xml)
#   - RBC (https://rssexport.rbc.ru/rbcnews/news/30/full.rss)
# США:
#   - WSJ (https://feeds.content.dowjones.io/public/rss/RSSUSnews)
#   - PBS NewsHour (https://www.pbs.org/newshour/feeds/rss/headlines)
#   - Politico (https://rss.politico.com/politics-news.xml)
#   - NYT (https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml)
# Китай:
#   - Xinhua (проверить актуальный RSS)
# После добавления — не забыть экспортировать в __init__.py
# и добавить класс в ALL_SOURCES.
