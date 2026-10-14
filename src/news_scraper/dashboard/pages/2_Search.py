from __future__ import annotations

import httpx
import streamlit as st

from news_scraper.dashboard._shared import API_BASE_URL, render_sidebar


def search_api(query: str, top_k: int) -> dict:
    """POST /search. Без кэша — запрос каждый раз новый."""
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f'{API_BASE_URL}/search',
            json={'query': query, 'top_k': top_k},
        )
        response.raise_for_status()
        return response.json()


def render_result(rank: int, result: dict) -> None:
    """Отображает одну историю с перепечатками."""
    st.markdown(f'### {rank}. {result["title"]}')
    st.caption(f'RRF score: {result["rrf_score"]:.4f}  •  [Открыть]({result["url"]})')
    st.markdown(result['text'][:500] + ('...' if len(result['text']) > 500 else ''))
    if result['related']:
        with st.expander(f'Перепечатки ({len(result["related"])})'):
            for rel in result['related']:
                st.markdown(f'- [{rel["id"]}] {rel["source"]}: {rel["url"]}')


def main() -> None:
    """Точка входа страницы Search."""
    st.set_page_config(page_title='Search — News Scraper', page_icon='🔍', layout='wide')
    st.title('🔍 Search')
    st.caption(
        'Семантический поиск: hybrid (BM25 + vector + RRF). Без LLM — только релевантные статьи.'
    )
    render_sidebar()
    with st.form('search_form'):
        query = st.text_input(
            'Поисковый запрос',
            placeholder='Например: ключевая ставка ЦБ',
            max_chars=500,
        )
        top_k = st.slider('Сколько результатов', 1, 20, 10)
        submitted = st.form_submit_button('Найти')
        if not submitted:
            st.info('Введите запрос. Например: «нефть ОПЕК», «ключевая ставка», «автопром Китая».')
            return
        if not query.strip():
            st.warning('Введите запрос.')
            return
        with st.spinner('Ищу...'):
            try:
                response = search_api(query, top_k)
            except Exception as exc:
                st.error(f'Ошибка: {exc}')
                return
            results = response.get('results', [])
            if not results:
                st.warning('Ничего не найдено.')
                return
            st.markdown(f'Найдено: **{len(results)}**')
            st.markdown('---')
            for i, result in enumerate(results, 1):
                render_result(i, result)
            st.markdown('---')


if __name__ == '__main__':
    main()
