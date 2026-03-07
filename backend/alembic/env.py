import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.db.database import Base, get_database_url
from app.features.auth.models import User
from app.features.outbox.models import OutboxEvent
from app.features.rbac.models import Permission, Role, RoleInheritance, RolePermission, UserRole

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Keep explicit model references so Alembic sees all tables in metadata.
_MODEL_REGISTRY = (User, Role, Permission, UserRole, RolePermission, RoleInheritance, OutboxEvent)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    database_url = get_database_url()
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    database_url = get_database_url()
    connectable = create_async_engine(
        url=database_url,
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
