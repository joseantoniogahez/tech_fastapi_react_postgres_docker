from app.core.common.records import (
    PermissionRecord,
    RoleInheritanceRecord,
    RolePermissionRecord,
    RoleRecord,
    UserRecord,
)
from app.core.errors.services import InvalidInputError
from app.features.rbac.schemas import (
    AdminUserResult,
    AssignedRoleResult,
    AssignedUserResult,
    PermissionResult,
    RolePermissionResult,
    RoleResult,
)


def normalize_role_name(name: str) -> str:
    normalized_name = name.strip().lower()
    if not normalized_name:
        raise InvalidInputError(message="Role name is required")
    return normalized_name


def build_permission_name_map(permissions: list[PermissionRecord]) -> dict[str, str]:
    return {permission.id: permission.name for permission in permissions}


def group_role_permissions(
    role_permissions: list[RolePermissionRecord],
) -> dict[int, list[RolePermissionRecord]]:
    permissions_by_role_id: dict[int, list[RolePermissionRecord]] = {}
    for role_permission in role_permissions:
        permissions_by_role_id.setdefault(role_permission.role_id, []).append(role_permission)
    return permissions_by_role_id


def group_parent_role_ids(
    role_inheritances: list[RoleInheritanceRecord],
) -> dict[int, list[int]]:
    parent_role_ids_by_role_id: dict[int, list[int]] = {}
    for role_inheritance in role_inheritances:
        parent_role_ids_by_role_id.setdefault(role_inheritance.role_id, []).append(role_inheritance.parent_role_id)

    for role_id, parent_role_ids in parent_role_ids_by_role_id.items():
        parent_role_ids_by_role_id[role_id] = sorted(parent_role_ids)

    return parent_role_ids_by_role_id


def to_permission_results(permissions: list[PermissionRecord]) -> list[PermissionResult]:
    return [PermissionResult(id=permission.id, name=permission.name) for permission in permissions]


def to_role_permission_result(
    role_permission: RolePermissionRecord,
    permission_names: dict[str, str],
) -> RolePermissionResult:
    return RolePermissionResult(
        id=role_permission.permission_id,
        name=permission_names.get(role_permission.permission_id, role_permission.permission_id),
        scope=role_permission.scope,
    )


def to_role_result(
    role: RoleRecord,
    role_permissions: list[RolePermissionRecord],
    permission_names: dict[str, str],
    parent_role_ids: list[int] | tuple[int, ...] = (),
) -> RoleResult:
    return RoleResult(
        id=role.id,
        name=role.name,
        permissions=[
            to_role_permission_result(role_permission, permission_names) for role_permission in role_permissions
        ],
        parent_role_ids=list(parent_role_ids),
    )


def to_assigned_role_results(roles: list[RoleRecord]) -> list[AssignedRoleResult]:
    return [AssignedRoleResult(id=role.id, name=role.name) for role in roles]


def to_assigned_user_results(users: list[UserRecord]) -> list[AssignedUserResult]:
    return [
        AssignedUserResult(
            id=user.id,
            username=user.username,
            disabled=user.disabled,
        )
        for user in users
    ]


def to_admin_user_result(user: UserRecord, *, role_ids: list[int] | tuple[int, ...]) -> AdminUserResult:
    return AdminUserResult(
        id=user.id,
        username=user.username,
        disabled=user.disabled,
        role_ids=list(role_ids),
    )
