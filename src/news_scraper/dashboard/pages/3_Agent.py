"""Страница Agent: LangGraph-агент с multi-step reasoning."""

from __future__ import annotations

import streamlit as st

from news_scraper.dashboard._shared import render_sidebar, stream_agent
from news_scraper.domain.enums import Category


def main() -> None:
    """Точка входа страницы Agent."""
    st.set_page_config(page_title='Agent — News Scraper', page_icon='🤖', layout='wide')
    st.title('🤖 Agent')
    st.caption('Multi-step анализ: агент сам решает, какие статьи искать и как их сравнить.')
    render_sidebar()

    with st.expander('📚 Доступные категории для анализа'):
        st.markdown(
            'Агент умеет анализировать тональность и метрики по следующим секторам (используйте английские названия):'
        )
        # Выводим категории в красивом виде
        cats = [c.value for c in Category if c.value != 'other']
        cols = st.columns(3)
        for i, cat in enumerate(cats):
            cols[i % 3].code(cat)

    with st.form('agent_form'):
        question = st.text_input(
            'Вопрос',
            placeholder='Например: Сравни ситуацию с нефтью и газом в России',
            max_chars=500,
        )
        submitted = st.form_submit_button('Спросить агента')

    if not submitted:
        st.info('Задайте сложный вопрос. Например: «Сравни ключевую ставку и инфляцию».')
        return

    if not question.strip():
        st.warning('Введите вопрос.')
        return

    st.markdown('### Ответ')

    # stream_agent будет yield-ить токены, а статусы печатать через st.info
    with st.spinner('Агент работает...'):
        st.write_stream(stream_agent(question))


if __name__ == '__main__':
    main()
