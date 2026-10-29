from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from news_scraper.db.base import Base


class Article(Base):
    """Сохранённая новость из источника.
    Уникальность обеспечивается двумя ключами:
    - url — уникален по источнику;
    - content_hash — SHA-256 от нормализованного содержимого,
    ловит дубли с разными URL.
    content_hash — grouping key для перепечаток (не UNIQUE),
    embedding — вектор bge-m3 (1024d).
    category_raw — исходное сырое значение из RSS (для отладки).
    category_predicted — категория, предсказанная LLM (заполняется асинхронно).
    category — результат маппинга через _CATEGORY_MAP.
    sentiment — тональность статьи (positive, neutral, negative).
    entities — извлеченные сущности в формате JSON: [{"text": "Компания", "type": "ORG"}, ...].
    market_impact — влияние на рынок в разрезе категорий.
    """

    __tablename__ = 'articles'
    __table_args__ = (
        Index(
            'ix_articles_embedding_hnsw',
            'embedding',
            postgresql_using='hnsw',
            postgresql_ops={'embedding': 'vector_cosine_ops'},
            postgresql_with={'m': 16, 'ef_construction': 64},
        ),
        Index(
            'ix_articles_tsv_ru',
            text("to_tsvector('russian'::regconfig, (title::text || ' '::text) || text)"),
            postgresql_using='gin',
        ),
        Index(
            'ix_articles_tsv_en',
            text("to_tsvector('english'::regconfig, (title::text || ' '::text) || text)"),
            postgresql_using='gin',
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(64), index=True)
    country: Mapped[str] = mapped_column(String(16), index=True)
    category_raw: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    category_predicted: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(32), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    text: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1024),
        nullable=True,
    )
    sentiment: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        index=True,
    )
    entities: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    market_impact: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
