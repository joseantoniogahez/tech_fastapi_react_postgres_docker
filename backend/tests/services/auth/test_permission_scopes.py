import asyncio
from unittest.mock import MagicMock

import pytest

from app.const.permission import PermissionId, PermissionScope
from app.services.permission_evaluator import PermissionEvaluator
from utils.testing_support.auth_service import build_service


def test_user_has_permission_delegates_scope_evaluation_after_loading_grant() -> None:
    permission_evaluator = MagicMock()
    permission_evaluator.normalize_required_scope.return_value = PermissionScope.TENANT
    permission_evaluator.is_granted_scope_allowed.return_value = True
    service, repository = build_service(permission_evaluator=permission_evaluator)
    repository.get_user_permission_scope.return_value = PermissionScope.ANY

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=3,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=" TENANT ",
            user_tenant_id=4,
            resource_tenant_id=4,
            resource_owner_id=9,
        )

        assert has_permission is True
        permission_evaluator.normalize_required_scope.assert_called_once_with(" TENANT ")
        repository.get_user_permission_scope.assert_awaited_once_with(
            user_id=3,
            permission_id=PermissionId.BOOK_UPDATE,
        )
        permission_evaluator.is_granted_scope_allowed.assert_called_once_with(
            granted_scope=PermissionScope.ANY,
            required_scope=PermissionScope.TENANT,
            user_id=3,
            resource_owner_id=9,
            user_tenant_id=4,
            resource_tenant_id=4,
        )

    asyncio.run(run_test())


def test_user_has_permission_passes_missing_grant_to_evaluator() -> None:
    permission_evaluator = MagicMock()
    permission_evaluator.normalize_required_scope.return_value = PermissionScope.OWN
    permission_evaluator.is_granted_scope_allowed.return_value = False
    service, repository = build_service(permission_evaluator=permission_evaluator)
    repository.get_user_permission_scope.return_value = None

    async def run_test() -> None:
        has_permission = await service.user_has_permission(
            user_id=7,
            permission_id=PermissionId.BOOK_UPDATE,
            required_scope=PermissionScope.OWN,
            resource_owner_id=7,
        )

        assert has_permission is False
        permission_evaluator.is_granted_scope_allowed.assert_called_once_with(
            granted_scope=None,
            required_scope=PermissionScope.OWN,
            user_id=7,
            resource_owner_id=7,
            user_tenant_id=None,
            resource_tenant_id=None,
        )

    asyncio.run(run_test())


def test_user_has_permission_raises_for_invalid_required_scope_before_loading_grant() -> None:
    service, repository = build_service(permission_evaluator=PermissionEvaluator())

    async def run_test() -> None:
        with pytest.raises(ValueError, match="Invalid permission scope 'regional'"):
            await service.user_has_permission(
                user_id=12,
                permission_id=PermissionId.BOOK_UPDATE,
                required_scope="regional",
                resource_owner_id=None,
                user_tenant_id=None,
                resource_tenant_id=None,
            )

        repository.get_user_permission_scope.assert_not_awaited()

    asyncio.run(run_test())
