from collections.abc import Iterable

from app.core.authorization import PERMISSION_SCOPE_RANK
from app.core.common.records import RoleInheritanceRecord, RolePermissionRecord


def merge_scope(current_scope: str | None, candidate_scope: str) -> str:
    if current_scope is None:
        return candidate_scope
    if PERMISSION_SCOPE_RANK.get(candidate_scope, -1) > PERMISSION_SCOPE_RANK.get(current_scope, -1):
        return candidate_scope
    return current_scope


def build_direct_permission_map(role_permissions: Iterable[RolePermissionRecord]) -> dict[int, dict[str, str]]:
    direct_permissions: dict[int, dict[str, str]] = {}
    for role_permission in role_permissions:
        if role_permission.scope not in PERMISSION_SCOPE_RANK:
            continue

        role_permissions_map = direct_permissions.setdefault(role_permission.role_id, {})
        existing_scope = role_permissions_map.get(role_permission.permission_id)
        role_permissions_map[role_permission.permission_id] = merge_scope(
            existing_scope,
            role_permission.scope,
        )
    return direct_permissions


def build_parents_map(role_inheritances: Iterable[RoleInheritanceRecord]) -> dict[int, tuple[int, ...]]:
    parents_by_role_id: dict[int, tuple[int, ...]] = {}
    for role_inheritance in role_inheritances:
        current_parents = parents_by_role_id.get(role_inheritance.role_id, ())
        parents_by_role_id[role_inheritance.role_id] = current_parents + (role_inheritance.parent_role_id,)
    return parents_by_role_id


def _resolve_target_role_ids(
    *,
    role_ids: tuple[int, ...] | None,
    direct_permissions_by_role_id: dict[int, dict[str, str]],
    parents_by_role_id: dict[int, tuple[int, ...]],
) -> list[int]:
    if role_ids is None:
        return sorted(set(direct_permissions_by_role_id) | set(parents_by_role_id))
    return sorted(set(role_ids))


def _resolve_effective_permissions_for_role(
    *,
    role_id: int,
    parents_by_role_id: dict[int, tuple[int, ...]],
    direct_permissions_by_role_id: dict[int, dict[str, str]],
    memoized_effective_permissions: dict[int, dict[str, str]],
    resolving_role_ids: set[int],
) -> dict[str, str]:
    cached = memoized_effective_permissions.get(role_id)
    if cached is not None:
        return cached
    if role_id in resolving_role_ids:
        return {}

    resolving_role_ids.add(role_id)
    effective_permissions = dict(direct_permissions_by_role_id.get(role_id, {}))
    for parent_role_id in parents_by_role_id.get(role_id, ()):
        parent_permissions = _resolve_effective_permissions_for_role(
            role_id=parent_role_id,
            parents_by_role_id=parents_by_role_id,
            direct_permissions_by_role_id=direct_permissions_by_role_id,
            memoized_effective_permissions=memoized_effective_permissions,
            resolving_role_ids=resolving_role_ids,
        )
        for permission_id, parent_scope in parent_permissions.items():
            existing_scope = effective_permissions.get(permission_id)
            effective_permissions[permission_id] = merge_scope(existing_scope, parent_scope)

    resolving_role_ids.remove(role_id)
    memoized_effective_permissions[role_id] = effective_permissions
    return effective_permissions


def resolve_effective_role_permissions(
    *,
    role_permissions: Iterable[RolePermissionRecord],
    role_inheritances: Iterable[RoleInheritanceRecord],
    role_ids: tuple[int, ...] | None = None,
) -> list[RolePermissionRecord]:
    if role_ids == ():
        return []

    parents_by_role_id = build_parents_map(role_inheritances)
    direct_permissions_by_role_id = build_direct_permission_map(role_permissions)
    target_role_ids = _resolve_target_role_ids(
        role_ids=role_ids,
        direct_permissions_by_role_id=direct_permissions_by_role_id,
        parents_by_role_id=parents_by_role_id,
    )

    memoized_effective_permissions: dict[int, dict[str, str]] = {}
    resolving_role_ids: set[int] = set()
    effective_role_permissions: list[RolePermissionRecord] = []
    for role_id in target_role_ids:
        effective_permissions = _resolve_effective_permissions_for_role(
            role_id=role_id,
            parents_by_role_id=parents_by_role_id,
            direct_permissions_by_role_id=direct_permissions_by_role_id,
            memoized_effective_permissions=memoized_effective_permissions,
            resolving_role_ids=resolving_role_ids,
        )
        for permission_id in sorted(effective_permissions):
            effective_role_permissions.append(
                RolePermissionRecord(
                    role_id=role_id,
                    permission_id=permission_id,
                    scope=effective_permissions[permission_id],
                )
            )
    return effective_role_permissions
