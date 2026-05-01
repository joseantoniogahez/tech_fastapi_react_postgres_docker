import asyncio
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.core.errors.repositories import RepositoryConflictError
from app.core.errors.services import ConflictError, InvalidInputError, UnauthorizedError
from app.features.auth.models import User
from app.features.rbac.models import Role, RoleInheritance
from app.features.rbac.schemas import (
    CreateAdminUserCommand,
    CreateRoleCommand,
    UpdateAdminUserCommand,
    UpdateRoleCommand,
)
from app.features.rbac.service import RBACService
from app.features.rbac.service_mappers import normalize_role_name


def _build_repository_mock() -> MagicMock:
    repository = MagicMock()
    repository.list_users = AsyncMock(return_value=[])
    repository.list_roles = AsyncMock(return_value=[])
    repository.list_permissions = AsyncMock(return_value=[])
    repository.list_role_permissions = AsyncMock(return_value=[])
    repository.list_role_inheritances = AsyncMock(return_value=[])
    repository.get_role = AsyncMock(return_value=None)
    repository.role_name_exists = AsyncMock(return_value=False)
    repository.create_role = AsyncMock()
    repository.update_role = AsyncMock()
    repository.delete_role = AsyncMock()
    repository.get_permission = AsyncMock(return_value=None)
    repository.upsert_role_permission = AsyncMock()
    repository.delete_role_permission = AsyncMock()
    repository.get_user = AsyncMock(return_value=None)
    repository.username_exists = AsyncMock(return_value=False)
    repository.create_user = AsyncMock()
    repository.update_user = AsyncMock()
    repository.list_user_role_ids = AsyncMock(return_value=[])
    repository.assign_user_role = AsyncMock()
    repository.remove_user_role = AsyncMock()
    repository.list_user_roles = AsyncMock(return_value=[])
    repository.list_role_users = AsyncMock(return_value=[])
    repository.assign_role_inheritance = AsyncMock()
    repository.remove_role_inheritance = AsyncMock()
    return repository


def _build_unit_of_work_mock() -> MagicMock:
    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)
    return unit_of_work


def _build_service() -> tuple[RBACService, MagicMock, MagicMock]:
    repository = _build_repository_mock()
    unit_of_work = _build_unit_of_work_mock()
    service = RBACService(rbac_repository=repository, unit_of_work=unit_of_work)
    return service, repository, unit_of_work


def test_normalize_role_name_raises_for_blank_value() -> None:
    with pytest.raises(InvalidInputError) as exc_info:
        normalize_role_name("   ")

    assert "Role name is required" in str(exc_info.value)


def test_list_roles_returns_empty_without_fetching_permissions() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        roles = await service.list_roles()

        assert roles == []
        repository.list_roles.assert_awaited_once_with()
        repository.list_permissions.assert_not_awaited()
        repository.list_role_permissions.assert_not_awaited()
        repository.list_role_inheritances.assert_not_awaited()

    asyncio.run(run_test())


def test_create_role_propagates_repository_conflict() -> None:
    service, repository, _ = _build_service()
    repository.create_role.side_effect = RepositoryConflictError(
        message="Role name already exists",
        details={"name": "ops_role"},
    )

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await service.create_role(CreateRoleCommand(name="ops_role"))

        assert "Role name already exists" in str(exc_info.value)
        assert exc_info.value.details == {"name": "ops_role"}
        repository.role_name_exists.assert_awaited_once_with("ops_role")

    asyncio.run(run_test())


def test_list_roles_uses_effective_permissions() -> None:
    service, repository, _ = _build_service()
    repository.list_roles.return_value = [Role(id=2, name="editor_role")]
    repository.list_role_inheritances.return_value = [RoleInheritance(role_id=2, parent_role_id=1)]

    async def run_test() -> None:
        roles = await service.list_roles()

        assert len(roles) == 1
        assert roles[0].parent_role_ids == [1]
        repository.list_role_permissions.assert_awaited_once_with()
        repository.list_role_inheritances.assert_awaited_once_with()

    asyncio.run(run_test())


def test_list_effective_role_permissions_fetches_inheritances_when_not_provided() -> None:
    service, repository, _ = _build_service()
    repository.list_role_permissions.return_value = []
    repository.list_role_inheritances.return_value = []

    async def run_test() -> None:
        role_permissions = (
            await service._role_operations._list_effective_role_permissions()  # pyright: ignore[reportPrivateUsage]
        )

        assert role_permissions == []
        repository.list_role_permissions.assert_awaited_once_with()
        repository.list_role_inheritances.assert_awaited_once_with()

    asyncio.run(run_test())


def test_update_role_propagates_repository_conflict() -> None:
    service, repository, _ = _build_service()
    repository.get_role.return_value = Role(id=7, name="ops_role")
    repository.update_role.side_effect = RepositoryConflictError(
        message="Role name already exists",
        details={"name": "ops_role_v2"},
    )

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await service.update_role(7, UpdateRoleCommand(name="ops_role_v2"))

        assert "Role name already exists" in str(exc_info.value)
        assert exc_info.value.details == {"name": "ops_role_v2"}
        repository.get_role.assert_awaited_once_with(7)
        repository.role_name_exists.assert_awaited_once_with(
            "ops_role_v2",
            exclude_role_id=7,
        )

    asyncio.run(run_test())


def test_assign_role_inheritance_rejects_self_inheritance() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="Role cannot inherit from itself"):
            await service.assign_role_inheritance(4, 4)

        repository.get_role.assert_not_awaited()
        repository.assign_role_inheritance.assert_not_awaited()

    asyncio.run(run_test())


def test_assign_role_inheritance_rejects_cycle() -> None:
    service, repository, _ = _build_service()
    repository.get_role.side_effect = [
        Role(id=2, name="child"),
        Role(id=1, name="parent"),
    ]
    repository.list_role_inheritances.return_value = [RoleInheritance(role_id=1, parent_role_id=2)]

    async def run_test() -> None:
        with pytest.raises(ConflictError) as exc_info:
            await service.assign_role_inheritance(2, 1)

        assert str(exc_info.value) == "Role inheritance cycle detected"
        assert exc_info.value.details == {"role_id": 2, "parent_role_id": 1}
        repository.assign_role_inheritance.assert_not_awaited()

    asyncio.run(run_test())


def test_assign_role_inheritance_is_idempotent_when_link_exists() -> None:
    service, repository, _ = _build_service()
    repository.get_role.side_effect = [
        Role(id=4, name="child"),
        Role(id=2, name="parent"),
    ]
    repository.list_role_inheritances.return_value = [RoleInheritance(role_id=4, parent_role_id=2)]

    async def run_test() -> None:
        await service.assign_role_inheritance(4, 2)

        repository.assign_role_inheritance.assert_not_awaited()

    asyncio.run(run_test())


def test_role_reaches_target_skips_already_visited_nodes() -> None:
    service, _, _ = _build_service()
    reaches_target = service._role_operations._role_reaches_target(  # pyright: ignore[reportPrivateUsage]
        parents_by_role_id={
            1: (2, 3),
            2: (4,),
            3: (4,),
            4: (),
        },
        start_role_id=1,
        target_role_id=5,
    )

    assert reaches_target is False


def test_list_user_roles_returns_assigned_roles() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    repository.list_user_roles.return_value = [Role(id=2, name="reader_role")]

    async def run_test() -> None:
        roles = await service.list_user_roles(3)

        assert [role.model_dump() for role in roles] == [{"id": 2, "name": "reader_role"}]
        repository.get_user.assert_awaited_once_with(3)
        repository.list_user_roles.assert_awaited_once_with(user_id=3)

    asyncio.run(run_test())


def test_list_role_users_returns_assigned_users() -> None:
    service, repository, _ = _build_service()
    repository.get_role.return_value = Role(id=2, name="reader_role")
    repository.list_role_users.return_value = [
        User(id=3, username="reader_user", hashed_password="hash", disabled=False)  # pragma: allowlist secret
    ]

    async def run_test() -> None:
        users = await service.list_role_users(2)

        assert [user.model_dump() for user in users] == [{"id": 3, "username": "reader_user", "disabled": False}]
        repository.get_role.assert_awaited_once_with(2)
        repository.list_role_users.assert_awaited_once_with(role_id=2)

    asyncio.run(run_test())


def test_list_users_returns_role_ids() -> None:
    service, repository, _ = _build_service()
    repository.list_users.return_value = [
        User(id=1, username="admin", hashed_password="hash", disabled=False),  # pragma: allowlist secret
        User(id=3, username="reader_user", hashed_password="hash", disabled=False),  # pragma: allowlist secret
    ]
    repository.list_user_role_ids.side_effect = [[1], [2]]

    async def run_test() -> None:
        users = await service.list_users()

        assert [user.model_dump() for user in users] == [
            {"id": 1, "username": "admin", "disabled": False, "role_ids": [1]},
            {"id": 3, "username": "reader_user", "disabled": False, "role_ids": [2]},
        ]
        repository.list_users.assert_awaited_once_with()
        assert repository.list_user_role_ids.await_count == 2

    asyncio.run(run_test())


def test_create_user_normalizes_username_and_assigns_roles() -> None:
    service, repository, _ = _build_service()
    repository.get_role.side_effect = [Role(id=1, name="admin_role"), Role(id=2, name="reader_role")]
    repository.create_user.return_value = User(id=7, username="ops_user", hashed_password="hash", disabled=False)
    repository.get_user.return_value = User(id=7, username="ops_user", hashed_password="hash", disabled=False)
    repository.list_user_role_ids.return_value = [1, 2]

    async def run_test() -> None:
        user = await service.create_user(
            CreateAdminUserCommand(
                username=" Ops_User ",
                password="OpsUser123",  # pragma: allowlist secret
                role_ids=[2, 1, 2],
            )
        )

        assert user.model_dump() == {
            "id": 7,
            "username": "ops_user",
            "disabled": False,
            "role_ids": [1, 2],
        }
        repository.username_exists.assert_awaited_once_with("ops_user")
        repository.assign_user_role.assert_has_awaits(
            [
                call(user_id=7, role_id=1),
                call(user_id=7, role_id=2),
            ]
        )

    asyncio.run(run_test())


def test_create_user_reuses_password_policy_validation() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="Password does not meet policy"):
            await service.create_user(
                CreateAdminUserCommand(
                    username="ops_user",
                    password="short",  # pragma: allowlist secret
                    role_ids=[],
                )
            )

        repository.username_exists.assert_not_awaited()
        repository.create_user.assert_not_awaited()

    asyncio.run(run_test())


def test_create_user_rejects_invalid_role_ids() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="role_ids must contain positive integers"):
            await service.create_user(
                CreateAdminUserCommand(
                    username="ops_user",
                    password="OpsUser123",  # pragma: allowlist secret
                    role_ids=[0, 2],
                )
            )

        repository.username_exists.assert_not_awaited()
        repository.create_user.assert_not_awaited()

    asyncio.run(run_test())


def test_create_user_rejects_blank_username() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="Username is required"):
            await service.create_user(
                CreateAdminUserCommand(
                    username="   ",
                    password="OpsUser123",  # pragma: allowlist secret
                    role_ids=[],
                )
            )

        repository.username_exists.assert_not_awaited()

    asyncio.run(run_test())


def test_create_user_rejects_invalid_username_format() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="Username has invalid format"):
            await service.create_user(
                CreateAdminUserCommand(
                    username="bad user",
                    password="OpsUser123",  # pragma: allowlist secret
                    role_ids=[],
                )
            )

        repository.username_exists.assert_not_awaited()

    asyncio.run(run_test())


def test_create_user_raises_conflict_when_username_exists() -> None:
    service, repository, _ = _build_service()
    repository.username_exists.return_value = True

    async def run_test() -> None:
        with pytest.raises(ConflictError) as exc_info:
            await service.create_user(
                CreateAdminUserCommand(
                    username="ops_user",
                    password="OpsUser123",  # pragma: allowlist secret
                    role_ids=[],
                )
            )

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "ops_user"}
        repository.create_user.assert_not_awaited()

    asyncio.run(run_test())


def test_update_user_requires_at_least_one_field() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="At least one field must be provided to update the user"):
            await service.update_user(3, UpdateAdminUserCommand())

        repository.get_user.assert_not_awaited()

    asyncio.run(run_test())


def test_update_user_requires_new_password_when_current_password_is_provided() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="new_password is required"):
            await service.update_user(
                3,
                UpdateAdminUserCommand(current_password="CurrentPass123"),  # pragma: allowlist secret
            )

        repository.get_user.assert_not_awaited()

    asyncio.run(run_test())


def test_update_user_requires_current_password_when_new_password_is_provided() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="current_password is required"):
            await service.update_user(
                3,
                UpdateAdminUserCommand(new_password="NewPass123"),  # pragma: allowlist secret
            )

        repository.get_user.assert_not_awaited()

    asyncio.run(run_test())


def test_apply_password_update_requires_current_password_when_new_password_is_provided() -> None:
    service, repository, _ = _build_service()
    user = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    changes: dict[str, object] = {}

    with pytest.raises(InvalidInputError, match="current_password is required"):
        service._user_management._apply_password_update(  # pyright: ignore[reportPrivateUsage]
            user=user,
            current_password=None,
            new_password="NewPass123",  # pragma: allowlist secret
            normalized_username="reader_user",
            changes=changes,
        )

    assert changes == {}
    repository.update_user.assert_not_awaited()


def test_update_user_replaces_role_set() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    repository.get_role.side_effect = [Role(id=2, name="editor_role"), Role(id=3, name="auditor_role")]
    repository.list_user_role_ids.side_effect = [[1, 2], [2, 3]]

    async def run_test() -> None:
        updated_user = await service.update_user(
            3,
            UpdateAdminUserCommand(role_ids=[3, 2, 3]),
        )

        assert updated_user.model_dump() == {
            "id": 3,
            "username": "reader_user",
            "disabled": False,
            "role_ids": [2, 3],
        }
        repository.remove_user_role.assert_awaited_once_with(user_id=3, role_id=1)
        repository.assign_user_role.assert_awaited_once_with(user_id=3, role_id=3)

    asyncio.run(run_test())


def test_update_user_keeps_same_username_without_conflict_lookup() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    repository.list_user_role_ids.return_value = [2]

    async def run_test() -> None:
        updated_user = await service.update_user(
            3,
            UpdateAdminUserCommand(username="reader_user"),
        )

        assert updated_user.model_dump() == {
            "id": 3,
            "username": "reader_user",
            "disabled": False,
            "role_ids": [2],
        }
        repository.username_exists.assert_not_awaited()
        repository.update_user.assert_not_awaited()

    asyncio.run(run_test())


def test_update_user_raises_conflict_when_new_username_is_taken() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    repository.username_exists.return_value = True

    async def run_test() -> None:
        with pytest.raises(ConflictError) as exc_info:
            await service.update_user(
                3,
                UpdateAdminUserCommand(username="ops_user"),
            )

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "ops_user"}
        repository.update_user.assert_not_awaited()

    asyncio.run(run_test())


def test_update_user_rejects_invalid_current_password() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=False)

    password_service = MagicMock()
    password_service.verify_password.side_effect = [False]
    service._user_management._password_service = password_service  # pyright: ignore[reportPrivateUsage]

    async def run_test() -> None:
        with pytest.raises(UnauthorizedError, match="Current password is invalid"):
            await service.update_user(
                3,
                UpdateAdminUserCommand(
                    current_password="CurrentPass123",  # pragma: allowlist secret
                    new_password="NewPass123",  # pragma: allowlist secret
                ),
            )

        repository.update_user.assert_not_awaited()

    asyncio.run(run_test())


def test_update_user_rejects_reusing_current_password() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=False)

    password_service = MagicMock()
    password_service.verify_password.side_effect = [True, True]
    service._user_management._password_service = password_service  # pyright: ignore[reportPrivateUsage]

    async def run_test() -> None:
        with pytest.raises(InvalidInputError, match="New password must be different from current password"):
            await service.update_user(
                3,
                UpdateAdminUserCommand(
                    current_password="CurrentPass123",  # pragma: allowlist secret
                    new_password="CurrentPass123",  # pragma: allowlist secret
                ),
            )

        repository.update_user.assert_not_awaited()

    asyncio.run(run_test())


def test_update_user_applies_disabled_toggle() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=False)
    repository.list_user_role_ids.return_value = [2]

    async def run_test() -> None:
        updated_user = await service.update_user(
            3,
            UpdateAdminUserCommand(disabled=True),
        )

        assert updated_user.model_dump() == {
            "id": 3,
            "username": "reader_user",
            "disabled": False,
            "role_ids": [2],
        }
        repository.update_user.assert_awaited_once_with(3, disabled=True)

    asyncio.run(run_test())


def test_delete_user_soft_delete_updates_disabled_flag() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=False)

    async def run_test() -> None:
        await service.delete_user(3)

        repository.update_user.assert_awaited_once_with(3, disabled=True)

    asyncio.run(run_test())


def test_delete_user_soft_delete_is_idempotent_for_already_disabled_user() -> None:
    service, repository, _ = _build_service()
    repository.get_user.return_value = User(id=3, username="reader_user", hashed_password="hash", disabled=True)

    async def run_test() -> None:
        await service.delete_user(3)

        repository.update_user.assert_not_awaited()

    asyncio.run(run_test())
