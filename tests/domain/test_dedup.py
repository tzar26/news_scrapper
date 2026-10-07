from datetime import UTC, datetime

import pytest

from news_scraper.domain.dedup import content_hash
from news_scraper.domain.enums import Category, Country
from news_scraper.domain.models import RawNewsItem


def make_item(title, text, url: str = None):
    url = url or f'https://example.com/{title}'
    return RawNewsItem(
        url=url,
        title=title,
        text=text,
        category=Category.ECONOMY,
        country=Country.USA,
        published_at=datetime.now(UTC),
        source='Example',
        summary='Example summary',
    )


@pytest.mark.parametrize(
    'title, text, expected_hash',
    [
        ('Hello', 'World', '26c60a61d01db5836ca70fefd44a6a016620413c8ef5f259a6c5612d4f79d3b8'),
        ('a  b', 'a\n b', '9f7a5681d8327860600e69fbbca79e02dcb54814a8a04ec0bf264344666b61e3'),
        (
            'Leading and trailing whitespace',
            '  text  ',
            '0c24eb2bc3b97a17916828b91b950f630440fc9b216a38769ad2ab03ab1b7759',
        ),
        (
            'Case insensitive',
            'Hello',
            '455ec5b4b34543cf1c9f95900b9fe066e6d318479a14468752fc0914d43e9dbc',
        ),
        (
            'Different content',
            'World',
            '429f18865d6fca8f975cdc7db636cac6a4ce4d9926a12e093106cde018f05815',
        ),
    ],
)
def test_content_hash(title, text, expected_hash):
    url = f'https://example.com/{title}'
    item = make_item(title, text, url)
    actual_hash = content_hash(item)
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64
    assert all(c in '0123456789abcdef' for c in actual_hash)


def test_same_content_same_hash():
    item1 = make_item('Hello', 'World', 'https://example.com/1')
    item2 = make_item('Hello', 'World', 'https://example.com/2')
    assert content_hash(item1) == content_hash(item2)


def test_different_content_different_hash():
    item1 = make_item('Hello', 'World')
    item2 = make_item('Hello', 'Universe')
    assert content_hash(item1) != content_hash(item2)


def test_case_insensitive():
    item1 = make_item('Hello', 'World')
    item2 = make_item('hello', 'World')
    assert content_hash(item1) == content_hash(item2)


def test_whitespace_normalized():
    item1 = make_item('a  b', 'a\n b')
    item2 = make_item('a b', 'a\n b')
    assert content_hash(item1) == content_hash(item2)


def test_hash_is_hex_sha256():
    item = make_item('Hello', 'World')
    actual_hash = content_hash(item)
    assert len(actual_hash) == 64
    assert all(c in '0123456789abcdef' for c in actual_hash)


def test_leading_trailing_whitespace_ignored():
    item1 = make_item('  text  ', 'World')
    item2 = make_item('text', 'World')
    assert content_hash(item1) == content_hash(item2)
