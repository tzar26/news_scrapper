"""add hnsw index on articles.embedding

Revision ID: dd3d5e09a756
Revises: 9d0091d44b03
Create Date: 2026-10-09 18:39:41.587434

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'dd3d5e09a756'
down_revision: str | Sequence[str] | None = '9d0091d44b03'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE INDEX ix_articles_embedding_hnsw
        ON articles
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP INDEX IF EXISTS ix_articles_embedding_hnsw')
