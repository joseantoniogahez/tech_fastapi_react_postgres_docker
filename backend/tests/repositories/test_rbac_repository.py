import asyncio

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions.repositories import RepositoryConflictError
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole
from app.repositories.rbac import RBACRepository
from utils.testing_support.repositories import build_session_mock


def test_rbac_repository_list_role_permissions_skips_query_for_empty_role_ids() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        role_permissions = await repository.list_role_permissions(role_ids=())

        assert role_permissions == []
        session.execute.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_delete_role_returns_false_when_role_does_not_exist() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.get.return_value = None

    async def run_test() -> None:
        deleted = await repository.delete_role(55)

        assert deleted is False
        session.get.assert_awaited_once_with(repository.model, 55)
        session.execute.assert_not_awaited()
        session.delete.assert_not_called()
        session.flush.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_upsert_role_permission_updates_existing_assignment() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    existing_assignment = RolePermission(
        role_id=4,
        permission_id="books:create",
        scope="own",
    )
    session.get.return_value = existing_assignment

    async def run_test() -> None:
        role_permission = await repository.upsert_role_permission(
            role_id=4,
            permission_id="books:create",
            scope="tenant",
        )

        assert role_permission is existing_assignment
        assert role_permission.scope == "tenant"
        session.add.assert_not_called()
        session.flush.assert_awaited_once()

    asyncio.run(run_test())


def test_rbac_repository_delete_role_permission_returns_false_when_missing() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.get.return_value = None

    async def run_test() -> None:
        deleted = await repository.delete_role_permission(
            role_id=8,
            permission_id="books:delete",
        )

        assert deleted is False
        session.delete.assert_not_called()
        session.flush.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_assign_user_role_returns_false_when_assignment_exists() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.get.return_value = UserRole(user_id=3, role_id=2)

    async def run_test() -> None:
        assigned = await repository.assign_user_role(user_id=3, role_id=2)

        assert assigned is False
        session.add.assert_not_called()
        session.flush.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_remove_user_role_returns_false_when_assignment_missing() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.get.return_value = None

    async def run_test() -> None:
        removed = await repository.remove_user_role(user_id=3, role_id=2)

        assert removed is False
        session.delete.assert_not_called()
        session.flush.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_create_role_translates_integrity_error_to_repository_conflict() -> None:
    session = build_session_mock()
    session.flush.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await repository.create_role(name="ops_role")

        assert "Role name already exists" in str(exc_info.value)
        assert exc_info.value.details == {"name": "ops_role"}
        session.refresh.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_update_role_translates_integrity_error_to_repository_conflict() -> None:
    session = build_session_mock()
    session.flush.side_effect = IntegrityError("update", {}, Exception("duplicate"))
    role = Role(id=4, name="ops_role")
    session.merge.return_value = role
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await repository.update_role(role, name="ops_role_v2")

        assert "Role name already exists" in str(exc_info.value)
        assert exc_info.value.details == {"name": "ops_role_v2"}
        session.refresh.assert_not_awaited()

    asyncio.run(run_test())
