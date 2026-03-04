"""Migrate timestamps to timezone-aware UTC

Revision ID: 8d44df6ce298
Revises: 2b9cf2b8d3a4
Create Date: 2026-02-25 10:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8d44df6ce298"
down_revision: str | None = "2b9cf2b8d3a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES_WITH_TIMESTAMPS = ("authors", "books", "users", "roles", "permissions")
_TIMESTAMP_COLUMNS = ("created_at", "updated_at")
_UTC_SERVER_DEFAULT = sa.text("CURRENT_TIMESTAMP")


def _upgrade_postgres() -> None:
    for table_name in _TABLES_WITH_TIMESTAMPS:
        for column_name in _TIMESTAMP_COLUMNS:
            op.alter_column(
                table_name,
                column_name,
                existing_type=sa.DateTime(timezone=False),
                type_=sa.DateTime(timezone=True),
                postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
                existing_nullable=False,
            )
            op.alter_column(
                table_name,
                column_name,
                existing_type=sa.DateTime(timezone=True),
                server_default=_UTC_SERVER_DEFAULT,
                existing_nullable=False,
            )


def _upgrade_generic() -> None:
    for table_name in _TABLES_WITH_TIMESTAMPS:
        with op.batch_alter_table(table_name) as batch_op:
            for column_name in _TIMESTAMP_COLUMNS:
                batch_op.alter_column(
                    column_name,
                    existing_type=sa.DateTime(timezone=False),
                    type_=sa.DateTime(timezone=True),
                    server_default=_UTC_SERVER_DEFAULT,
                    existing_nullable=False,
                )


def _downgrade_postgres() -> None:
    for table_name in _TABLES_WITH_TIMESTAMPS:
        for column_name in _TIMESTAMP_COLUMNS:
            op.alter_column(
                table_name,
                column_name,
                existing_type=sa.DateTime(timezone=True),
                server_default=None,
                existing_nullable=False,
            )
            op.alter_column(
                table_name,
                column_name,
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(timezone=False),
                postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
                existing_nullable=False,
            )


def _downgrade_generic() -> None:
    for table_name in _TABLES_WITH_TIMESTAMPS:
        with op.batch_alter_table(table_name) as batch_op:
            for column_name in _TIMESTAMP_COLUMNS:
                batch_op.alter_column(
                    column_name,
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.DateTime(timezone=False),
                    server_default=None,
                    existing_nullable=False,
                )


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        _upgrade_postgres()
        return
    _upgrade_generic()


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        _downgrade_postgres()
        return
    _downgrade_generic()
