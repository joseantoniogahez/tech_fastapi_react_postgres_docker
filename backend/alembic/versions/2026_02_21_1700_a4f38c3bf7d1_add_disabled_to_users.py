"""Add disabled column to users

Revision ID: a4f38c3bf7d1
Revises: 9c2a7e18b6f0
Create Date: 2026-02-21 17:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4f38c3bf7d1"
down_revision: Union[str, None] = "9c2a7e18b6f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "disabled")
