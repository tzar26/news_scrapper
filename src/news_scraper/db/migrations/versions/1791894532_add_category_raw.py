"""add category_raw

Revision ID: 33d99bb1b3ae
Revises: c8b9d0e0f70b
Create Date: 2026-10-13 17:28:52.207420

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '33d99bb1b3ae'
down_revision: str | Sequence[str] | None = 'c8b9d0e0f70b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Добавляет category_raw — что буквально прислал RSS-фид.

    Отладочное поле, не индексируется, nullable.
    """
    op.add_column(
        'articles',
        sa.Column('category_raw', sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    """Удаляет category_raw."""
    op.drop_column('articles', 'category_raw')
