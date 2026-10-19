from __future__ import annotations

import json
import os
from datetime import datetime

import httpx
import streamlit as st

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')


@st.cache_data(ttl=30)
def fetch_stats() -> dict:
    """Забирает агрегированную статистику из FastAPI /stats."""
    with httpx.Client(timeout=10.0) as client:
        response = client.get(f'{API_BASE_URL}/stats')
        response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60)
def fetch_health() -> dict:
    """Проверяет доступность API через /health."""
    with httpx.Client(timeout=5.0) as client:
        response = client.get(f'{API_BASE_URL}/health')
        response.raise_for_status()
    return response.json()


def ask_question(question: str, top_k: int = 5, rerank: bool = False) -> dict:
    """Отправляет вопрос в POST /ask. Не кэшируется — вопрос каждый раз новый.
    Timeout 90 секунд — rerank медленнее.
    """
    with httpx.Client(timeout=90.0) as client:
        response = client.post(
            f'{API_BASE_URL}/ask',
            json={'question': question, 'top_k': top_k, 'rerank': rerank},
        )
        response.raise_for_status()
    return response.json()


def format_date(iso_str: str) -> str:
    """Форматирует ISO datetime в 'DD.MM.YYYY HH:MM'."""
    return datetime.fromisoformat(iso_str.replace('Z', '+00:00')).strftime('%d.%m.%Y %H:%M')


def render_sidebar() -> None:
    """Сайдбар: статус API, ссылки, кнопка обновления."""
    with st.sidebar:
        st.header('News Scraper')
        st.caption('Pet-проект: сбор и анализ новостей')
        try:
            health = fetch_health()
            st.success(f'API: {health["status"]}')
        except Exception as exc:
            st.error(f'API недоступен: {exc}')
        st.markdown('---')
        st.markdown(f'[API docs]({API_BASE_URL}/docs)')
        st.markdown('---')
        if st.button('Обновить данные'):
            st.cache_data.clear()
            st.rerun()


def ask_agent(question: str) -> dict:
    """Отправляет вопрос в POST /agent."""
    with httpx.Client(timeout=120.0) as client:  # агент может думать долго
        response = client.post(
            f'{API_BASE_URL}/agent',
            json={'question': question},
        )
        response.raise_for_status()
        return response.json()


def stream_ask(question: str, top_k: int = 5, rerank: bool = False):
    """Генератор для st.write_stream.

    Читает SSE от /ask/stream. Кусочки текста отдаёт в yield.
    Источники сохраняет в st.session_state['sources'].
    """
    import streamlit as st

    st.session_state['sources'] = []

    payload = {'question': question, 'top_k': top_k, 'rerank': rerank}

    with httpx.stream(
        'POST', f'{API_BASE_URL}/ask/stream', json=payload, timeout=120.0
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith('data: '):
                continue

            chunk = line[6:]  # убираем префикс 'data: '

            if chunk.startswith('\\n\\n__SOURCES__'):
                sources_json = chunk.replace('\\n\\n__SOURCES__', '')
                st.session_state['sources'] = json.loads(sources_json)
                break

            # Возвращаем экранированные переносы строк обратно
            yield chunk.replace('\\n', '\n')
