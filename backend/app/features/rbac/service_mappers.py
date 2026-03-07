from app.core.common.records import PermissionRecord, RolePermissionRecord, RoleRecord
from app.core.errors.services import InvalidInputError
from app.features.rbac.schemas import PermissionResult, RolePermissionResult, RoleResult


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
) -> RoleResult:
    return RoleResult(
        id=role.id,
        name=role.name,
        permissions=[
            to_role_permission_result(role_permission, permission_names) for role_permission in role_permissions
        ],
    )
