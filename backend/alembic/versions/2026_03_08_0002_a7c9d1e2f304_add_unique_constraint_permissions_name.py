"""Add unique constraint on permissions.name

Revision ID: a7c9d1e2f304
Revises: f1a2b3c4d5e6
Create Date: 2026-03-08 15:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c9d1e2f304"
down_revision: str | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_permissions_name",
        "permissions",
        ["name"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_permissions_name",
        "permissions",
        type_="unique",
    )
