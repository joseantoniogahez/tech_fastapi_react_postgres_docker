import asyncio

from app.const.permission import PermissionId, PermissionScope
from utils.testing_support.auth_service import build_service


def test_user_has_permission_allows_any_scope_for_global_requirement() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = PermissionScope.ANY

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=1,
            permission_id=PermissionId.BOOK_CREATE,
            required_scope=PermissionScope.ANY,
        )

        assert has_permission is True
        repository.get_user_permission_scope.assert_awaited_once_with(
            user_id=1,
            permission_id=PermissionId.BOOK_CREATE,
        )

    asyncio.run(run_test())


def test_user_has_permission_denies_when_required_scope_is_any_and_grant_is_tenant() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = PermissionScope.TENANT

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=1,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=PermissionScope.ANY,
            user_tenant_id=11,
            resource_tenant_id=11,
        )

        assert has_permission is False

    asyncio.run(run_test())


def test_user_has_permission_allows_own_scope_for_self_service() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = PermissionScope.OWN

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=7,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=PermissionScope.OWN,
            resource_owner_id=7,
        )

        assert has_permission is True

    asyncio.run(run_test())


def test_user_has_permission_denies_own_scope_for_other_owner() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = PermissionScope.OWN

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=7,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=PermissionScope.OWN,
            resource_owner_id=8,
        )

        assert has_permission is False

    asyncio.run(run_test())


def test_user_has_permission_allows_tenant_scope_for_matching_tenant() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = PermissionScope.TENANT

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=3,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=PermissionScope.TENANT,
            user_tenant_id=4,
            resource_tenant_id=4,
        )

        assert has_permission is True

    asyncio.run(run_test())


def test_user_has_permission_denies_tenant_scope_for_mismatched_tenant() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = PermissionScope.TENANT

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=3,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=PermissionScope.TENANT,
            user_tenant_id=4,
            resource_tenant_id=9,
        )

        assert has_permission is False

    asyncio.run(run_test())


def test_user_has_permission_allows_tenant_grant_for_own_requirement_with_owner_context() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = PermissionScope.TENANT

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=3,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=PermissionScope.OWN,
            resource_owner_id=3,
            user_tenant_id=4,
            resource_tenant_id=None,
        )

        assert has_permission is True

    asyncio.run(run_test())


def test_user_has_permission_denies_invalid_granted_scope() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = "regional"

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=1,
            permission_id=PermissionId.BOOK_CREATE,
            required_scope=PermissionScope.OWN,
            resource_owner_id=1,
        )

        assert has_permission is False

    asyncio.run(run_test())


def test_user_has_permission_allows_any_grant_for_own_requirement() -> None:
    service, repository = build_service()
    repository.get_user_permission_scope.return_value = PermissionScope.ANY

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=12,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=PermissionScope.OWN,
            resource_owner_id=None,
            user_tenant_id=None,
            resource_tenant_id=None,
        )

        assert has_permission is True

    asyncio.run(run_test())
