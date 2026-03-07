"""Initial template baseline

Revision ID: f1a2b3c4d5e6
Revises:
Create Date: 2026-03-06 00:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UTC_SERVER_DEFAULT = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_UTC_SERVER_DEFAULT),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_UTC_SERVER_DEFAULT),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_UTC_SERVER_DEFAULT),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_UTC_SERVER_DEFAULT),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_UTC_SERVER_DEFAULT),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_UTC_SERVER_DEFAULT),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.String(length=100), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False, server_default="any"),
        sa.CheckConstraint("scope IN ('own', 'tenant', 'any')", name="ck_role_permissions_scope"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    op.create_table(
        "role_inheritances",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("parent_role_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("role_id <> parent_role_id", name="ck_role_inheritances_not_self"),
        sa.ForeignKeyConstraint(["parent_role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("role_id", "parent_role_id"),
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=150), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_UTC_SERVER_DEFAULT),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_UTC_SERVER_DEFAULT),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_outbox_events_published_at_id",
        "outbox_events",
        ["published_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_events_published_at_id", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_table("role_inheritances")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
