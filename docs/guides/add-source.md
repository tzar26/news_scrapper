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
- ✅ Kommersant
- ✅ TASS
- ✅ RBC
- ✅ Interfax
- ✅ Prime

### США
- ✅ NPR
- ✅ WSJ
- ✅ CNBC
- ✅ MarketWatch
- ✅ PBS NewsHour
- ✅ NYT
- ⚠️ CNN — мёртвый RSS, удалён

### Китай
- ✅ Xinhua
- ✅ Global Times
- ⚠️ China Daily — RSS не работает (404), не используем

### Мир (без страны)
- ✅ OilPrice

### Отложенные
- ⏳ Politico — битая ссылка, проверить позже

## Проблема: Xinhua timeout

Первый прогон скрапера упал на Xinhua с `httpx.ReadTimeout`.
Повторный — прошёл. Это **временный сетевой сбой**, не проблема кода.

**Решения:**
1. **Оставить как есть** — редкий кейс, `try/except` в `scrape_all_sources`
   ловит и продолжает. Источник помечен как `failed`, повторится
   на следующем прогоне beat'а.
2. **Добавить retry в `RSSSource.fetch()`** — 3 попытки с backoff.
   Правильно, но это работа на будущее.

**Решение сейчас:** оставляем как есть. Если Xinhua будет падать
часто — добавим retry.

## Что делать, если источник не-RSS

Источник всё равно реализует Protocol `Source`, но использует
свой парсер. См. `docs/decisions/003-multiple-rss-sources.md`.

Пока таких нет. Когда появится — здесь будет отдельный гайд.
