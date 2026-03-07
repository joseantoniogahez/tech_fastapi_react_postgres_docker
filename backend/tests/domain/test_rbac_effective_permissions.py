from app.features.rbac.effective_permissions import (
    build_direct_permission_map,
    merge_scope,
    resolve_effective_role_permissions,
)
from app.features.rbac.models import RoleInheritance, RolePermission


def test_merge_scope_keeps_current_when_candidate_is_not_broader() -> None:
    assert merge_scope("tenant", "own") == "tenant"


def test_build_direct_permission_map_skips_invalid_scope() -> None:
    permission_map = build_direct_permission_map(
        [
            RolePermission(role_id=1, permission_id="roles:manage", scope="any"),
            RolePermission(role_id=1, permission_id="user_roles:manage", scope="regional"),
        ]
    )

    assert permission_map == {
        1: {
            "roles:manage": "any",
        }
    }


def test_resolve_effective_role_permissions_returns_empty_for_empty_role_ids() -> None:
    effective_permissions = resolve_effective_role_permissions(
        role_permissions=[],
        role_inheritances=[],
        role_ids=(),
    )

    assert effective_permissions == []


def test_resolve_effective_role_permissions_includes_inherited_permissions() -> None:
    direct_permissions = [
        RolePermission(role_id=2, permission_id="roles:manage", scope="own"),
        RolePermission(role_id=1, permission_id="roles:manage", scope="tenant"),
        RolePermission(role_id=1, permission_id="user_roles:manage", scope="any"),
    ]
    inheritances = [RoleInheritance(role_id=2, parent_role_id=1)]

    effective_permissions = resolve_effective_role_permissions(
        role_permissions=direct_permissions,
        role_inheritances=inheritances,
        role_ids=(2,),
    )

    by_permission = {permission.permission_id: permission.scope for permission in effective_permissions}
    assert by_permission == {
        "roles:manage": "tenant",
        "user_roles:manage": "any",
    }
    assert all(permission.role_id == 2 for permission in effective_permissions)


def test_resolve_effective_role_permissions_handles_cycles() -> None:
    direct_permissions = [
        RolePermission(role_id=1, permission_id="roles:manage", scope="own"),
        RolePermission(role_id=2, permission_id="role_permissions:manage", scope="tenant"),
    ]
    inheritances = [
        RoleInheritance(role_id=1, parent_role_id=2),
        RoleInheritance(role_id=2, parent_role_id=1),
    ]

    effective_permissions = resolve_effective_role_permissions(
        role_permissions=direct_permissions,
        role_inheritances=inheritances,
        role_ids=(1,),
    )

    by_permission = {permission.permission_id: permission.scope for permission in effective_permissions}
    assert by_permission == {
        "roles:manage": "own",
        "role_permissions:manage": "tenant",
    }


def test_resolve_effective_role_permissions_without_role_filter_uses_all_referenced_roles() -> None:
    direct_permissions = [
        RolePermission(role_id=2, permission_id="roles:manage", scope="tenant"),
    ]
    inheritances = [
        RoleInheritance(role_id=1, parent_role_id=2),
    ]

    effective_permissions = resolve_effective_role_permissions(
        role_permissions=direct_permissions,
        role_inheritances=inheritances,
    )

    grouped: dict[int, dict[str, str]] = {}
    for permission in effective_permissions:
        grouped.setdefault(permission.role_id, {})[permission.permission_id] = permission.scope

    assert grouped == {
        1: {"roles:manage": "tenant"},
        2: {"roles:manage": "tenant"},
    }
