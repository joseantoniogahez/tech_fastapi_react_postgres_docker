import asyncio

from app.dependencies.authorization import (
    build_current_tenant_permission_context,
    build_current_user_permission_context,
    build_default_permission_context,
)
from app.models.user import User


def _build_user(*, user_id: int, tenant_id: int | None) -> User:
    return User(
        id=user_id,
        username="dependency-user",
        hashed_password="hash",
        disabled=False,
        tenant_id=tenant_id,
    )


def test_build_default_permission_context_returns_empty_context() -> None:
    async def run_test() -> None:
        context = await build_default_permission_context()

        assert context.owner_user_id is None
        assert context.tenant_id is None

    asyncio.run(run_test())


def test_build_current_user_permission_context_maps_owner_and_tenant() -> None:
    current_user = _build_user(user_id=7, tenant_id=11)

    async def run_test() -> None:
        context = await build_current_user_permission_context(current_user)

        assert context.owner_user_id == 7
        assert context.tenant_id == 11

    asyncio.run(run_test())


def test_build_current_tenant_permission_context_maps_tenant_only() -> None:
    current_user = _build_user(user_id=9, tenant_id=22)

    async def run_test() -> None:
        context = await build_current_tenant_permission_context(current_user)

        assert context.owner_user_id is None
        assert context.tenant_id == 22

    asyncio.run(run_test())
