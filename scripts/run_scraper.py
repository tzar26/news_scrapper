from __future__ import annotations

import asyncio

from news_scraper.scraper.sources.kommersant import KommersantSource


async def main():
    source = KommersantSource()
    articles = await source.fetch()
    print(f'Found {len(articles)} articles')
    for article in articles[:3]:
        print(f'{article.published_at}: {article.title}')
    await source.aclose()


if __name__ == '__main__':
    asyncio.run(main())
