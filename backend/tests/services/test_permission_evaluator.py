from unittest.mock import patch

import pytest

from app.core.authorization import PermissionScope
from app.core.authorization.permission_evaluator import PermissionEvaluator


def test_normalize_required_scope_trims_and_lowercases() -> None:
    evaluator = PermissionEvaluator()

    assert evaluator.normalize_required_scope("  TENANT  ") == PermissionScope.TENANT


def test_normalize_required_scope_raises_for_invalid_scope() -> None:
    evaluator = PermissionEvaluator()

    with pytest.raises(ValueError, match="Invalid permission scope 'regional'"):
        evaluator.normalize_required_scope("regional")


def test_is_granted_scope_allowed_returns_false_when_grant_is_missing() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=None,
            required_scope=PermissionScope.ANY,
            user_id=1,
            resource_owner_id=None,
            user_tenant_id=None,
            resource_tenant_id=None,
        )
        is False
    )


def test_is_granted_scope_allowed_allows_any_scope_for_global_requirement() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.ANY,
            required_scope=PermissionScope.ANY,
            user_id=1,
            resource_owner_id=None,
            user_tenant_id=None,
            resource_tenant_id=None,
        )
        is True
    )


def test_is_granted_scope_allowed_denies_when_required_scope_is_any_and_grant_is_tenant() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.TENANT,
            required_scope=PermissionScope.ANY,
            user_id=1,
            resource_owner_id=None,
            user_tenant_id=11,
            resource_tenant_id=11,
        )
        is False
    )


def test_is_granted_scope_allowed_allows_own_scope_for_self_service() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.OWN,
            required_scope=PermissionScope.OWN,
            user_id=7,
            resource_owner_id=7,
            user_tenant_id=None,
            resource_tenant_id=None,
        )
        is True
    )


def test_is_granted_scope_allowed_denies_own_scope_for_other_owner() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.OWN,
            required_scope=PermissionScope.OWN,
            user_id=7,
            resource_owner_id=8,
            user_tenant_id=None,
            resource_tenant_id=None,
        )
        is False
    )


def test_is_granted_scope_allowed_allows_tenant_scope_for_matching_tenant() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.TENANT,
            required_scope=PermissionScope.TENANT,
            user_id=3,
            resource_owner_id=None,
            user_tenant_id=4,
            resource_tenant_id=4,
        )
        is True
    )


def test_is_granted_scope_allowed_denies_tenant_scope_for_mismatched_tenant() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.TENANT,
            required_scope=PermissionScope.TENANT,
            user_id=3,
            resource_owner_id=None,
            user_tenant_id=4,
            resource_tenant_id=9,
        )
        is False
    )


def test_is_granted_scope_allowed_allows_tenant_grant_for_own_requirement_with_owner_context() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.TENANT,
            required_scope=PermissionScope.OWN,
            user_id=3,
            resource_owner_id=3,
            user_tenant_id=4,
            resource_tenant_id=None,
        )
        is True
    )


def test_is_granted_scope_allowed_denies_invalid_granted_scope() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope="regional",
            required_scope=PermissionScope.OWN,
            user_id=1,
            resource_owner_id=1,
            user_tenant_id=None,
            resource_tenant_id=None,
        )
        is False
    )


def test_is_granted_scope_allowed_allows_any_grant_for_own_requirement() -> None:
    evaluator = PermissionEvaluator()

    assert (
        evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.ANY,
            required_scope=PermissionScope.OWN,
            user_id=12,
            resource_owner_id=None,
            user_tenant_id=None,
            resource_tenant_id=None,
        )
        is True
    )


def test_scope_evaluator_defensive_fallback_returns_false_for_unknown_required_scope() -> None:
    evaluator = PermissionEvaluator()

    # Simula una futura expansion de scopes para ejecutar la rama defensiva actual.
    with patch.dict("app.core.authorization.permission_evaluator.PERMISSION_SCOPE_RANK", {"regional": 2}, clear=False):
        allowed = evaluator.is_granted_scope_allowed(
            granted_scope=PermissionScope.ANY,
            required_scope="regional",
            user_id=1,
            resource_owner_id=1,
            user_tenant_id=1,
            resource_tenant_id=1,
        )

    assert allowed is False
