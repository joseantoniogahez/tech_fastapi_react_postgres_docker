import asyncio
import tempfile

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from utils.database import MockDatabase
from utils.rbac_bootstrap import BASE_PERMISSION_SPECS, BASE_ROLE_PERMISSION_SPECS, bootstrap_rbac


async def _count_rows(session: AsyncSession, model: type[object]) -> int:
    result = await session.execute(select(func.count()).select_from(model))
    return int(result.scalar_one())


def test_bootstrap_rbac_is_idempotent() -> None:
    async def run_test() -> None:
        with tempfile.TemporaryDirectory(prefix="backend-rbac-bootstrap-") as db_tmp_dir:
            mock_db = MockDatabase(path=db_tmp_dir, echo=False)
            await mock_db.setup(Base)
            try:
                first_run = await bootstrap_rbac(
                    mock_db.Session,
                    admin_username="admin",
                    admin_password="StrongSeed9",
                )
                second_run = await bootstrap_rbac(
                    mock_db.Session,
                    admin_username="admin",
                    admin_password=None,
                )

                assert first_run.permissions_created == len(BASE_PERMISSION_SPECS)
                assert first_run.permissions_updated == 0
                assert first_run.roles_created == len(BASE_ROLE_PERMISSION_SPECS)
                assert first_run.role_permissions_created == len(BASE_PERMISSION_SPECS)
                assert first_run.admin_user_created is True
                assert first_run.admin_role_assigned is True

                assert second_run.permissions_created == 0
                assert second_run.permissions_updated == 0
                assert second_run.roles_created == 0
                assert second_run.role_permissions_created == 0
                assert second_run.admin_user_created is False
                assert second_run.admin_role_assigned is False

                async with mock_db.Session() as session:
                    assert await _count_rows(session, Permission) == len(BASE_PERMISSION_SPECS)
                    assert await _count_rows(session, Role) == len(BASE_ROLE_PERMISSION_SPECS)
                    assert await _count_rows(session, RolePermission) == len(BASE_PERMISSION_SPECS)
                    assert await _count_rows(session, User) == 1
                    assert await _count_rows(session, UserRole) == 1

                    admin = await session.scalar(select(User).where(User.username == "admin"))
                    assert admin is not None
                    assert admin.disabled is False
                    assert admin.hashed_password != "StrongSeed9"
            finally:
                await mock_db.close()

    asyncio.run(run_test())


def test_bootstrap_requires_admin_password_if_admin_user_is_missing() -> None:
    async def run_test() -> None:
        with tempfile.TemporaryDirectory(prefix="backend-rbac-bootstrap-") as db_tmp_dir:
            mock_db = MockDatabase(path=db_tmp_dir, echo=False)
            await mock_db.setup(Base)
            try:
                with pytest.raises(
                    ValueError,
                    match="Admin user does not exist. Provide --admin-password or set RBAC_BOOTSTRAP_ADMIN_PASSWORD.",
                ):
                    await bootstrap_rbac(
                        mock_db.Session,
                        admin_username="admin",
                        admin_password=None,
                    )

                async with mock_db.Session() as session:
                    assert await _count_rows(session, Permission) == 0
                    assert await _count_rows(session, Role) == 0
                    assert await _count_rows(session, User) == 0
            finally:
                await mock_db.close()

    asyncio.run(run_test())
