"""Add players table

Revision ID: 771ccc10c556
Revises: 933c08b4970e
Create Date: 2025-08-11 19:06:13.066686

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "771ccc10c556"
down_revision: Union[str, None] = "933c08b4970e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "players",
        sa.Column("relic_id", sa.String(255), primary_key=True),
        sa.Column("discord", sa.String(255), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("players")
