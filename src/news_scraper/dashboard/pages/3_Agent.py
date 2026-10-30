"""Страница Agent: LangGraph-агент с multi-step reasoning и историей диалога."""

from __future__ import annotations

import streamlit as st

from news_scraper.dashboard._shared import render_sidebar, stream_agent


def main() -> None:
    """Точка входа страницы Agent."""
    st.set_page_config(page_title='Agent — News Scraper', page_icon='🤖', layout='wide')
    st.title('🤖 Agent')
    st.caption('Multi-step анализ: агент сам решает, какие статьи искать и как их сравнить.')
    render_sidebar()

    # Инициализируем историю в сессии (если её нет)
    if 'agent_history' not in st.session_state:
        st.session_state.agent_history = []

    # Кнопка очистки истории
    if st.button('Очистить историю'):
        st.session_state.agent_history = []
        st.rerun()

    # Отображаем историю диалога
    for msg in st.session_state.agent_history:
        role = 'user' if msg['role'] == 'user' else 'assistant'
        with st.chat_message(role):
            st.markdown(msg['content'])

    # Поле ввода
    if prompt := st.chat_input('Задайте вопрос агенту...'):
        # Показываем сообщение пользователя
        with st.chat_message('user'):
            st.markdown(prompt)

        # Добавляем в историю
        st.session_state.agent_history.append({'role': 'user', 'content': prompt})

        # Генерируем ответ
        with st.chat_message('assistant'), st.spinner('Агент работает...'):
            # Передаем историю (все сообщения КРОМЕ текущего prompt, чтобы не дублировать)
            history_to_pass = st.session_state.agent_history[:-1]

            # Запускаем стриминг
            response_text = st.write_stream(stream_agent(prompt, history=history_to_pass))

        # Сохраняем ответ агента в историю
        st.session_state.agent_history.append({'role': 'assistant', 'content': response_text})


if __name__ == '__main__':
    main()
