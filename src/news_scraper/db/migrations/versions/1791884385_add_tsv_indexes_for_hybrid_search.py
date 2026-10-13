"""add tsv indexes for hybrid search

Revision ID: c8b9d0e0f70b
Revises: dd3d5e09a756
Create Date: 2026-10-13 14:39:45.361480

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c8b9d0e0f70b'
down_revision: str | Sequence[str] | None = 'dd3d5e09a756'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создаёт GIN-индексы для полнотекстового поиска (BM25).

    Функциональные индексы на выражении to_tsvector:
    не дублируют данные, поддерживаются PostgreSQL автоматически.
    Отдельные индексы для русского и английского — контент смешанный.
    """
    op.execute(
        """
        CREATE INDEX ix_articles_tsv_ru
        ON articles
        USING gin (to_tsvector('russian', title || ' ' || text))
        """
    )
    op.execute(
        """
        CREATE INDEX ix_articles_tsv_en
        ON articles
        USING gin (to_tsvector('english', title || ' ' || text))
        """
    )


def downgrade() -> None:
    """Удаляет GIN-индексы."""
    op.execute('DROP INDEX IF EXISTS ix_articles_tsv_ru')
    op.execute('DROP INDEX IF EXISTS ix_articles_tsv_en')
