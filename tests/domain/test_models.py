from datetime import UTC, datetime

import pytest
from pydantic import HttpUrl, ValidationError

from news_scraper.domain.enums import Category, Country
from news_scraper.domain.models import RawNewsItem


def test_valid_item():
    item = RawNewsItem(
        url='https://example.com',
        title='Test Title',
        source='Test Source',
        country=Country.RUSSIA,
        category=Category.POLITICS,
        published_at=datetime.now(UTC),
        text='Test text',
    )
    assert item.title == 'Test Title'
    assert item.url == HttpUrl('https://example.com')
    assert item.source == 'Test Source'
    assert item.country == Country.RUSSIA
    assert item.category == Category.POLITICS
    assert item.published_at.tzinfo == UTC
    assert item.text == 'Test text'


def test_timezone_naive_rejected():
    with pytest.raises(ValidationError):
        RawNewsItem(
            url='https://example.com',
            title='Test Title',
            source='Test Source',
            country=Country.RUSSIA,
            category=Category.POLITICS,
            published_at=datetime.now(),  # No timezone
            text='Test text',
        )


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        RawNewsItem(
            url='https://example.com',
            title='Test Title',
            source='Test Source',
            country=Country.RUSSIA,
            category=Category.POLITICS,
            published_at=datetime.now(UTC),
            text='Test text',
            extra_field='extra',  # Extra field
        )


def test_invalid_url_rejected():
    with pytest.raises(ValidationError):
        RawNewsItem(
            url='not a url',  # Invalid URL
            title='Test Title',
            source='Test Source',
            country=Country.RUSSIA,
            category=Category.POLITICS,
            published_at=datetime.now(UTC),
            text='Test text',
        )


def test_summary_optional():
    item = RawNewsItem(
        url='https://example.com',
        title='Test Title',
        source='Test Source',
        country=Country.RUSSIA,
        category=Category.POLITICS,
        published_at=datetime.now(UTC),
        text='Test text',
        summary='Test Summary',
    )
    assert item.summary == 'Test Summary'


def test_str_strip_whitespace():
    item = RawNewsItem(
        url='https://example.com',
        title=' Test Title ',
        source='Test Source',
        country=Country.RUSSIA,
        category=Category.POLITICS,
        published_at=datetime.now(UTC),
        text=' Test text ',
    )
    assert item.title == 'Test Title'
