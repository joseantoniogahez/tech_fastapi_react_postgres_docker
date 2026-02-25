"""Add unique constraint to authors.name

Revision ID: 2b9cf2b8d3a4
Revises: f4b0d9a5c2e1
Create Date: 2026-02-25 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2b9cf2b8d3a4"
down_revision: Union[str, None] = "f4b0d9a5c2e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("authors") as batch_op:
        batch_op.create_unique_constraint("uq_authors_name", ["name"])


def downgrade() -> None:
    with op.batch_alter_table("authors") as batch_op:
        batch_op.drop_constraint("uq_authors_name", type_="unique")
