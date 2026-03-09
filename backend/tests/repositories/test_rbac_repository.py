import asyncio
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors.repositories import RepositoryConflictError, RepositoryError
from app.features.auth.models import User
from app.features.rbac.models import Permission, Role, RoleInheritance, RolePermission, UserRole
from app.features.rbac.repository import RBACRepository
from utils.testing_support.repositories import build_session_mock


def _scalar_result(rows: list[object]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


def test_rbac_repository_list_role_permissions_skips_query_for_empty_role_ids() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        role_permissions = await repository.list_role_permissions(role_ids=())

        assert role_permissions == []
        session.execute.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_list_role_permissions_filters_query_for_role_ids() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.execute.return_value = _scalar_result(
        [RolePermission(role_id=1, permission_id="roles:manage", scope="any")]
    )

    async def run_test() -> None:
        role_permissions = await repository.list_role_permissions(role_ids=(1,))

        assert len(role_permissions) == 1
        session.execute.assert_awaited_once()
        query = session.execute.await_args.args[0]
        assert "role_permissions.role_id IN" in str(query)

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
        permission_id="roles:manage",
        scope="own",
    )
    session.get.return_value = existing_assignment

    async def run_test() -> None:
        role_permission = await repository.upsert_role_permission(
            role_id=4,
            permission_id="roles:manage",
            scope="tenant",
        )

        assert role_permission.role_id == 4
        assert role_permission.permission_id == "roles:manage"
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
            permission_id="user_roles:manage",
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


def test_rbac_repository_list_user_roles_filters_by_user_id() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.execute.return_value = _scalar_result([Role(id=2, name="reader_role")])

    async def run_test() -> None:
        roles = await repository.list_user_roles(user_id=3)

        assert len(roles) == 1
        assert roles[0].id == 2
        assert roles[0].name == "reader_role"
        session.execute.assert_awaited_once()
        query = session.execute.await_args.args[0]
        assert "user_roles.user_id" in str(query)

    asyncio.run(run_test())


def test_rbac_repository_list_users_orders_by_username() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.execute.return_value = _scalar_result(
        [
            User(id=1, username="admin", hashed_password="hash", disabled=False),  # pragma: allowlist secret
            User(id=3, username="reader_user", hashed_password="hash", disabled=True),  # pragma: allowlist secret
        ]
    )

    async def run_test() -> None:
        users = await repository.list_users()

        assert [(user.id, user.username, user.disabled) for user in users] == [
            (1, "admin", False),
            (3, "reader_user", True),
        ]
        session.execute.assert_awaited_once()
        query = session.execute.await_args.args[0]
        assert "ORDER BY users.username ASC" in str(query)

    asyncio.run(run_test())


def test_rbac_repository_list_user_role_ids_returns_sorted_ids() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.execute.return_value = _scalar_result([1, 2, 4])

    async def run_test() -> None:
        role_ids = await repository.list_user_role_ids(user_id=3)

        assert role_ids == [1, 2, 4]
        session.execute.assert_awaited_once()
        query = session.execute.await_args.args[0]
        assert "user_roles.user_id" in str(query)
        assert "ORDER BY user_roles.role_id ASC" in str(query)

    asyncio.run(run_test())


def test_rbac_repository_list_role_users_filters_by_role_id() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.execute.return_value = _scalar_result(
        [User(id=3, username="reader_user", hashed_password="hash", disabled=False)]  # pragma: allowlist secret
    )

    async def run_test() -> None:
        users = await repository.list_role_users(role_id=2)

        assert len(users) == 1
        assert users[0].id == 3
        assert users[0].username == "reader_user"
        assert users[0].disabled is False
        session.execute.assert_awaited_once()
        query = session.execute.await_args.args[0]
        assert "user_roles.role_id" in str(query)

    asyncio.run(run_test())


def test_rbac_repository_create_user_translates_integrity_error_to_repository_conflict() -> None:
    session = build_session_mock()
    session.flush.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await repository.create_user(
                username="ops_user",
                hashed_password="hash",  # pragma: allowlist secret
                disabled=False,
            )

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "ops_user"}
        session.refresh.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_create_user_raises_repository_error_on_integrity_without_string_username() -> None:
    session = build_session_mock()
    session.flush.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryError, match="Failed to create user"):
            await repository.create_user(
                username=123,
                hashed_password="hash",  # pragma: allowlist secret
                disabled=False,
            )

        session.refresh.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_update_user_updates_columns() -> None:
    session = build_session_mock()
    user = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    session.get.return_value = user
    session.merge.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=True)
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        updated_user = await repository.update_user(3, disabled=True)

        assert (updated_user.id, updated_user.username, updated_user.disabled) == (3, "reader_user", True)
        assert user.disabled is True
        session.get.assert_awaited_once_with(User, 3)
        session.merge.assert_awaited_once()
        session.flush.assert_awaited_once()
        session.refresh.assert_awaited_once()

    asyncio.run(run_test())


def test_rbac_repository_update_user_raises_error_when_user_does_not_exist() -> None:
    session = build_session_mock()
    session.get.return_value = None
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryError, match="User 404 not found"):
            await repository.update_user(404, disabled=True)

        session.merge.assert_not_awaited()
        session.flush.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_update_user_rejects_unknown_column() -> None:
    session = build_session_mock()
    user = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    session.get.return_value = user
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryError, match="Column 'unknown_field' does not exist on 'User'"):
            await repository.update_user(3, unknown_field=True)

        session.merge.assert_not_awaited()
        session.flush.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_update_user_translates_integrity_error_to_repository_conflict() -> None:
    session = build_session_mock()
    user = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    session.get.return_value = user
    session.merge.return_value = user
    session.flush.side_effect = IntegrityError("update", {}, Exception("duplicate"))
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await repository.update_user(3, username="ops_user")

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "ops_user"}
        session.refresh.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_update_user_raises_repository_error_on_non_username_integrity_error() -> None:
    session = build_session_mock()
    user = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    session.get.return_value = user
    session.merge.return_value = user
    session.flush.side_effect = IntegrityError("update", {}, Exception("duplicate"))
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryError, match="Failed to update user"):
            await repository.update_user(3, disabled=True)

        session.refresh.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_list_role_inheritances_skips_query_for_empty_role_ids() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        role_inheritances = await repository.list_role_inheritances(role_ids=())

        assert role_inheritances == []
        session.execute.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_list_role_inheritances_filters_query_for_role_ids() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.execute.return_value = _scalar_result([RoleInheritance(role_id=2, parent_role_id=1)])

    async def run_test() -> None:
        role_inheritances = await repository.list_role_inheritances(role_ids=(2,))

        assert len(role_inheritances) == 1
        session.execute.assert_awaited_once()
        query = session.execute.await_args.args[0]
        assert "role_inheritances.role_id IN" in str(query)

    asyncio.run(run_test())


def test_rbac_repository_assign_role_inheritance_returns_false_when_assignment_exists() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.get.return_value = RoleInheritance(role_id=3, parent_role_id=2)

    async def run_test() -> None:
        assigned = await repository.assign_role_inheritance(role_id=3, parent_role_id=2)

        assert assigned is False
        session.add.assert_not_called()
        session.flush.assert_not_awaited()

    asyncio.run(run_test())


def test_rbac_repository_remove_role_inheritance_returns_false_when_assignment_missing() -> None:
    session = build_session_mock()
    repository = RBACRepository(session=session)
    session.get.return_value = None

    async def run_test() -> None:
        removed = await repository.remove_role_inheritance(role_id=3, parent_role_id=2)

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


def test_rbac_repository_update_role_raises_error_when_role_does_not_exist() -> None:
    session = build_session_mock()
    session.get.return_value = None
    repository = RBACRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryError) as exc_info:
            await repository.update_role(404, name="ops_role_v2")

        assert "Role 404 not found" in str(exc_info.value)
        session.merge.assert_not_awaited()
        session.flush.assert_not_awaited()

    asyncio.run(run_test())


def test_permission_model_marks_name_as_unique() -> None:
    assert Permission.__table__.c.name.unique is True
