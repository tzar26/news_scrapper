"""Страница Ask: задать вопрос по базе статей через RAG."""

from __future__ import annotations

import streamlit as st

from news_scraper.dashboard._shared import ask_question, render_sidebar, stream_ask


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
    st.set_page_config(page_title='Ask — News Scraper', page_icon='💬', layout='wide')
    st.title('💬 Ask')
    st.caption(
        'Задайте вопрос — система найдёт релевантные статьи (hybrid search) и сгенерирует ответ с цитатами.'
    )
    render_sidebar()

    with st.form('ask_form'):
        question = st.text_input(
            'Ваш вопрос',
            placeholder='Например: Что происходит с нефтью?',
            max_chars=500,
        )
        top_k = st.slider('Сколько статей подать в контекст', 1, 10, 5)

        col1, col2, col3 = st.columns(3)
        with col1:
            use_rerank = st.checkbox('Применить reranking', value=False)
        with col2:
            use_streaming = st.checkbox('Стриминг', value=True)
        with col3:
            period_str = st.selectbox('Период', ['Всё время', 'За 1 день', 'За 3 дня', 'За 7 дней'])
            days_ago_map = {'Всё время': None, 'За 1 день': 1, 'За 3 дня': 3, 'За 7 дней': 7}
            days_ago = days_ago_map[period_str]

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

    st.markdown('### Ответ')

    if use_streaming:
        # Стриминговый режим
        with st.spinner('Ищу и печатаю...'):
            st.write_stream(
                stream_ask(
                    question,
                    top_k=top_k,
                    rerank=use_rerank,
                    days_ago=days_ago,
                )
            )

        # Источники берём из session_state (их туда положил stream_ask)
        sources = st.session_state.get('sources', [])
    else:
        # Обычный режим
        with st.spinner('Ищу и генерирую ответ... (~10 сек)'):
            try:
                result = ask_question(
                    question,
                    top_k=top_k,
                    rerank=use_rerank,
                    days_ago=days_ago,
                )
            except Exception as exc:
                st.error(f'Ошибка: {exc}')
                return

        st.markdown(result['answer'])
        sources = result.get('sources', [])

    st.markdown('---')
    render_sources(sources)


if __name__ == '__main__':
    main()
