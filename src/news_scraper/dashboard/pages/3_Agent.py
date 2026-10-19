from __future__ import annotations

import streamlit as st

from news_scraper.dashboard._shared import ask_agent, render_sidebar


def main() -> None:
    """Точка входа страницы Agent."""
    st.set_page_config(page_title='Agent — News Scraper', page_icon='🤖', layout='wide')
    st.title('🤖 Agent')
    st.caption('Multi-step анализ: агент сам решает, какие статьи искать и как их сравнить.')
    render_sidebar()

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

        with st.spinner('Агент думает (может занять 15-20 сек)...'):
            try:
                result = ask_agent(question)
            except Exception as exc:
                st.error(f'Ошибка: {exc}')
                return

            st.markdown('### Ответ')
            st.markdown(result['answer'])
            st.caption(f'Шагов сделано: {result["iterations"]}')


if __name__ == '__main__':
    main()
