"""Диагностика доступности новых источников (RSS и Google News)."""

from __future__ import annotations

import asyncio

import httpx

SOURCES = {
    # Официальные RSS
    'Forbes Russia (офиц)': 'https://www.forbes.ru/rss',
    'SmartLab (офиц)': 'https://smart-lab.ru/rss/',
    'InvestFuture (офиц)': 'https://investfuture.ru/rss',
    'БКС Экспресс (офиц)': 'https://bcs-express.ru/rss',
    # Google News (поиск по сайту)
    'Forbes Russia (GNews)': 'https://news.google.com/rss/search?q=site:forbes.ru&hl=ru&gl=RU&ceid=RU:ru',
    'SmartLab (GNews)': 'https://news.google.com/rss/search?q=site:smart-lab.ru&hl=ru&gl=RU&ceid=RU:ru',
    'InvestFuture (GNews)': 'https://news.google.com/rss/search?q=site:investfuture.ru&hl=ru&gl=RU&ceid=RU:ru',
    'БКС Экспресс (GNews)': 'https://news.google.com/rss/search?q=site:bcs-express.ru&hl=ru&gl=RU&ceid=RU:ru',
}


async def check(name: str, url: str, client: httpx.AsyncClient) -> None:
    """Проверяет один URL."""
    try:
        response = await client.get(url, follow_redirects=True, timeout=10.0)

        # Проверяем, является ли контент XML (RSS)
        is_rss = b'<rss' in response.content[:500] or b'<feed' in response.content[:500]

        status = 'OK' if response.status_code == 200 else f'HTTP {response.status_code}'
        rss_status = 'RSS' if is_rss else 'NOT RSS (возможно HTML)'

        print(f'[{status:>3}] {rss_status:<18} {name}')
    except Exception as e:
        print(f'[ERR] {type(e).__name__:<18} {name}')


async def main() -> None:
    """Запускает проверку всех источников."""
    async with httpx.AsyncClient(headers={'User-Agent': 'Mozilla/5.0'}) as client:
        for name, url in SOURCES.items():
            await check(name, url, client)


if __name__ == '__main__':
    asyncio.run(main())
