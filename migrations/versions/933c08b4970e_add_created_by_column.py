"""Add created_by column

Revision ID: 933c08b4970e
Revises:
Create Date: 2025-05-19 01:58:40.437900

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "933c08b4970e"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tournaments", sa.Column("created_by", sa.String(255), default=None))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tournaments", "created_by")
