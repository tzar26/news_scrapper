# Как добавить новый RSS-источник

## Чеклист

1. **Создать файл** `src/news_scraper/scraper/sources/<name>.py`.

2. **Определить класс** по образцу:

    from news_scraper.domain.enums import Country
    from news_scraper.scraper.sources.rss import RSSSource

    class <Name>Source(RSSSource):
        """RSS-источник <Человекочитаемое имя>."""

        name = '<name>'
        country = Country.<COUNTRY>
        rss_url = '<url>'

    Ничего больше. Методы не переопределять без необходимости.

3. **Экспортировать в** `src/news_scraper/scraper/sources/__init__.py`:
   добавить импорт и имя в `__all__`.

4. **Добавить в реестр** `registry.py::ALL_SOURCES`.

5. **Проверить**:

    python -c "
    import asyncio
    from news_scraper.scraper.sources.<name> import <Name>Source

    async def main():
        s = <Name>Source()
        items = await s.fetch()
        print(f'<name>: {len(items)} articles')
        for it in items[:3]:
            print(' ', it.published_at, it.title[:70])
        await s.aclose()

    asyncio.run(main())
    "

   Ожидаемо: N > 0. Если 0 — проверить URL, кодировку, наличие
   `published_parsed` в ленте.

6. **Коммит**:

    git add src/news_scraper/scraper/sources/<name>.py \
            src/news_scraper/scraper/sources/__init__.py \
            src/news_scraper/scraper/sources/registry.py
    git commit -m "feat(scraper): add <name> source"

## Проверенные источники по странам

### Россия
- ✅ Kommersant — https://www.kommersant.ru/RSS/news.xml
- ⏳ TASS — https://tass.ru/rss/v2.xml
- ⏳ RBC — https://rssexport.rbc.ru/rbcnews/news/30/full.rss

### США
- ✅ NPR — https://feeds.npr.org/1001/rss.xml
- ✅ CNN — http://rss.cnn.com/rss/cnn_topstories.rss
- ⏳ WSJ — https://feeds.content.dowjones.io/public/rss/RSSUSnews
- ⏳ PBS NewsHour — https://www.pbs.org/newshour/feeds/rss/headlines
- ⏳ Politico — https://rss.politico.com/politics-news.xml
- ⏳ NYT — https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml

### Китай
- ⏳ Xinhua — проверить актуальный RSS

## Что делать, если источник не-RSS

Источник всё равно реализует Protocol `Source`, но использует
свой парсер. См. `docs/decisions/003-multiple-rss-sources.md`.

Пока таких нет. Когда появится — здесь будет отдельный гайд.
