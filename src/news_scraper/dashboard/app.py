from __future__ import annotations

import httpx
import streamlit as st

from news_scraper.dashboard._shared import API_BASE_URL, fetch_stats, format_date, render_sidebar


def render_overview(stats: dict) -> None:
    """Обзор: metric cards + диапазон дат."""
    st.subheader('Обзор')
    col1, col2, col3 = st.columns(3)
    col1.metric('Всего статей', stats['total_articles'])
    col2.metric('Источников', len(stats['by_source']))
    col3.metric('Стран', len(stats['by_country']))
    earliest = stats.get('earliest_published_at')
    latest = stats.get('latest_published_at')
    if earliest and latest:
        st.caption(f'Диапазон дат: {format_date(earliest)} — {format_date(latest)}')


def render_by_country(stats: dict) -> None:
    """Bar chart по странам."""
    st.subheader('По странам')
    data = {item['key']: item['count'] for item in stats['by_country']}
    st.bar_chart(data)


def render_by_source(stats: dict) -> None:
    """Bar chart по источникам."""
    st.subheader('По источникам')
    data = {item['key']: item['count'] for item in stats['by_source']}
    st.bar_chart(data)


def render_by_category(stats: dict) -> None:
    """Bar chart по категориям."""
    st.subheader('По категориям')
    st.caption(
        'Категория берётся из RSS-фида. Большинство источников '
        'её не передают — отсюда преобладание "other". '
        'Автоматическая классификация через LLM запланирована.'
    )
    data = {item['key']: item['count'] for item in stats['by_category']}
    st.bar_chart(data)


def main() -> None:
    """Точка входа главной страницы."""
    st.set_page_config(page_title='News Scraper', page_icon='📰', layout='wide')
    st.title('📰 News Scraper Dashboard')
    st.caption('Обзор собранных статей')
    render_sidebar()
    try:
        stats = fetch_stats()
    except Exception as exc:
        st.error(f'Не удалось загрузить статистику: {exc}')
        st.stop()
    render_overview(stats)
    st.markdown('---')
    col1, col2 = st.columns(2)
    with col1:
        render_by_country(stats)
    with col2:
        render_by_source(stats)
    st.markdown('---')
    render_by_category(stats)
    try:
        errors_resp = httpx.get(f'{API_BASE_URL}/health/source_errors', timeout=5.0)
        errors = errors_resp.json() if errors_resp.status_code == 200 else []
        if errors:
            st.warning(f'⚠️ Ошибки при сборе новостей ({len(errors)}):')
            for err in errors:
                st.markdown(f'- **{err["source"]}**: `{err["error"]}`')
    except Exception:
        pass  # Если API недоступен, не ломаем главную страницу


if __name__ == '__main__':
    main()
