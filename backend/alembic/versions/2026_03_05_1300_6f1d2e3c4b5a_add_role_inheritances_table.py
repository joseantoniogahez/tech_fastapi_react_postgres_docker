"""Add role inheritances table

Revision ID: 6f1d2e3c4b5a
Revises: 8d44df6ce298
Create Date: 2026-03-05 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6f1d2e3c4b5a"
down_revision: str | None = "8d44df6ce298"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "role_inheritances",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("parent_role_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("role_id <> parent_role_id", name="ck_role_inheritances_not_self"),
        sa.ForeignKeyConstraint(["parent_role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("role_id", "parent_role_id"),
    )


def downgrade() -> None:
    op.drop_table("role_inheritances")
