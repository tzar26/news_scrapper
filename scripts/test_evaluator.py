"""Тест оценки качества ответов (Faithfulness, Answer Relevance) на 5 вопросах."""

from __future__ import annotations

import asyncio

from news_scraper.db.session import SessionLocal
from news_scraper.rag.chains import answer_question
from news_scraper.rag.evaluator import evaluate_answer

# Специально подбираем разные типы запросов:
# 1. Точный факт (на который должен быть ответ)
# 2. Общий аналитический вопрос
# 3. Сложный составной запрос (РФ + США)
# 4. Вопрос, ответа на который нет в базе (проверка на галлюцинацию)
# 5. Запрос про конкретную компанию

QUESTIONS = [
    'Какая сейчас ключевая ставка ЦБ?',
    'Что происходит на рынке нефти?',
    'Сравни инфляцию в России и США.',
    'Какой прогноз курса биткоина на 2027 год?',  # <- Ответа нет, проверяем галлюцинации
    'Что пишут про Сбербанк?',
]


async def main() -> None:
    """Прогоняет 5 вопросов, оценивает и выводит средние метрики."""
    async with SessionLocal() as session:
        total_faithfulness = 0.0
        total_relevance = 0.0
        successful_evals = 0

        for i, question in enumerate(QUESTIONS, 1):
            print(f'\n{"=" * 80}')
            print(f'ВОПРОС {i}: {question}')
            print(f'{"=" * 80}')

            result = await answer_question(session, question, top_k=3)
            print(f'\nОтвет: {result.answer}')
            print(f'\nНайдено статей: {len(result.results)}')

            if not result.results:
                print('Оценка: пропущена (нет контекста для оценки).')
                continue

            contexts = [r.text for r in result.results]

            print('\nОценка качества...')
            scores = await evaluate_answer(question, result.answer, contexts)

            if not scores:
                print('Оценка не удалась.')
                continue

            f_score = scores.get('faithfulness', 0.0)
            r_score = scores.get('answer_relevance', 0.0)

            print(f'Faithfulness: {f_score:.2f}')
            print(f'Answer Relevance: {r_score:.2f}')
            print(f'Пояснение: {scores.get("reasoning", "")}')

            total_faithfulness += f_score
            total_relevance += r_score
            successful_evals += 1

        if successful_evals > 0:
            print(f'\n{"=" * 80}')
            print('=== ИТОГОВЫЕ СРЕДНИЕ ПОКАЗАТЕЛИ ===')
            print(f'Средний Faithfulness: {total_faithfulness / successful_evals:.2f}')
            print(f'Средний Answer Relevance: {total_relevance / successful_evals:.2f}')
            print(f'Оценено вопросов: {successful_evals} из {len(QUESTIONS)}')


if __name__ == '__main__':
    asyncio.run(main())
