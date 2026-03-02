import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions.repositories import RepositoryConflictException
from app.exceptions.services import InvalidInputException
from app.models.role import Role
from app.schemas.rbac import CreateRole, UpdateRole
from app.services.rbac import RBACService


def _build_repository_mock() -> MagicMock:
    repository = MagicMock()
    repository.list_roles = AsyncMock(return_value=[])
    repository.list_permissions = AsyncMock(return_value=[])
    repository.list_role_permissions = AsyncMock(return_value=[])
    repository.get_role = AsyncMock(return_value=None)
    repository.role_name_exists = AsyncMock(return_value=False)
    repository.create_role = AsyncMock()
    repository.update_role = AsyncMock()
    repository.delete_role = AsyncMock()
    repository.get_permission = AsyncMock(return_value=None)
    repository.upsert_role_permission = AsyncMock()
    repository.delete_role_permission = AsyncMock()
    repository.get_user = AsyncMock(return_value=None)
    repository.assign_user_role = AsyncMock()
    repository.remove_user_role = AsyncMock()
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
    service, _, _ = _build_service()

    with pytest.raises(InvalidInputException) as exc_info:
        service._normalize_role_name("   ")

    assert "Role name is required" in str(exc_info.value)


def test_list_roles_returns_empty_without_fetching_permissions() -> None:
    service, repository, _ = _build_service()

    async def run_test() -> None:
        roles = await service.list_roles()

        assert roles == []
        repository.list_roles.assert_awaited_once_with()
        repository.list_permissions.assert_not_awaited()
        repository.list_role_permissions.assert_not_awaited()

    asyncio.run(run_test())


def test_create_role_propagates_repository_conflict() -> None:
    service, repository, _ = _build_service()
    repository.create_role.side_effect = RepositoryConflictException(
        message="Role name already exists",
        details={"name": "ops_role"},
    )

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictException) as exc_info:
            await service.create_role(CreateRole(name="ops_role"))

        assert "Role name already exists" in str(exc_info.value)
        assert exc_info.value.details == {"name": "ops_role"}
        repository.role_name_exists.assert_awaited_once_with("ops_role")

    asyncio.run(run_test())


def test_update_role_propagates_repository_conflict() -> None:
    service, repository, _ = _build_service()
    repository.get_role.return_value = Role(id=7, name="ops_role")
    repository.update_role.side_effect = RepositoryConflictException(
        message="Role name already exists",
        details={"name": "ops_role_v2"},
    )

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictException) as exc_info:
            await service.update_role(7, UpdateRole(name="ops_role_v2"))

        assert "Role name already exists" in str(exc_info.value)
        assert exc_info.value.details == {"name": "ops_role_v2"}
        repository.get_role.assert_awaited_once_with(7)
        repository.role_name_exists.assert_awaited_once_with(
            "ops_role_v2",
            exclude_role_id=7,
        )

    asyncio.run(run_test())
