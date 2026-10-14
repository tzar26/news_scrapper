from __future__ import annotations

import os
from datetime import datetime

import httpx
import streamlit as st

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')


@st.cache_data(ttl=60)
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


def ask_question(question: str, top_k: int = 5) -> dict:
    """Отправляет вопрос в POST /ask. Не кэшируется — вопрос каждый раз новый.
    Timeout 60 секунд — LLM генерирует ответ 5-15 сек.
    """
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f'{API_BASE_URL}/ask',
            json={'question': question, 'top_k': top_k},
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
