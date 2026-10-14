"""Страница Ask: задать вопрос по базе статей через RAG."""

from __future__ import annotations

import time

import streamlit as st

from news_scraper.dashboard._shared import ask_question, render_sidebar


def render_sources(sources: list[dict]) -> None:
    """Отображает список источников в виде сворачиваемых блоков."""
    if not sources:
        st.info('Источники не найдены.')
        return

    st.subheader(f'Источники ({len(sources)})')
    for source in sources:
        with st.expander(f'[{source["id"]}] {source["title"][:80]}'):
            st.markdown(f'**URL:** [{source["url"]}]({source["url"]})')
            st.markdown(f'**ID:** `{source["id"]}`')


def main() -> None:
    """Точка входа страницы Ask."""
    st.set_page_config(
        page_title='Ask — News Scraper',
        page_icon='💬',
        layout='wide',
    )
    st.title('💬 Ask')
    st.caption(
        'Задайте вопрос — система найдёт релевантные статьи '
        '(hybrid search: BM25 + vector) и сгенерирует ответ с цитатами.'
    )
    render_sidebar()

    with st.form('ask_form'):
        question = st.text_input(
            'Ваш вопрос',
            placeholder='Например: Что происходит с нефтью?',
            max_chars=500,
        )
        top_k = st.slider('Сколько статей подать в контекст', 1, 10, 5)
        submitted = st.form_submit_button('Спросить')

    if not submitted:
        st.info(
            'Введите вопрос в поле выше. '
            'Например: «Что влияет на рынок нефти?», '
            '«Что нового с ключевой ставкой ЦБ?»'
        )
        return

    if not question.strip():
        st.warning('Введите вопрос.')
        return

    with st.spinner('Ищу релевантные статьи и генерирую ответ... (~10 сек)'):
        start = time.monotonic()
        try:
            result = ask_question(question, top_k=top_k)
        except Exception as exc:
            st.error(f'Ошибка: {exc}')
            return
        elapsed = time.monotonic() - start

    st.markdown('### Ответ')
    st.markdown(result['answer'])

    st.markdown('---')
    render_sources(result.get('sources', []))
    st.caption(f'⏱️ {elapsed:.2f}s')


if __name__ == '__main__':
    main()
