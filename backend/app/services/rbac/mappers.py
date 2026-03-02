from app.exceptions.services import InvalidInputException
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.schemas.application.rbac import PermissionResult, RolePermissionResult, RoleResult


def normalize_role_name(name: str) -> str:
    normalized_name = name.strip().lower()
    if not normalized_name:
        raise InvalidInputException(message="Role name is required")
    return normalized_name


def build_permission_name_map(permissions: list[Permission]) -> dict[str, str]:
    return {permission.id: permission.name for permission in permissions}


def group_role_permissions(
    role_permissions: list[RolePermission],
) -> dict[int, list[RolePermission]]:
    permissions_by_role_id: dict[int, list[RolePermission]] = {}
    for role_permission in role_permissions:
        permissions_by_role_id.setdefault(role_permission.role_id, []).append(role_permission)
    return permissions_by_role_id


def to_permission_results(permissions: list[Permission]) -> list[PermissionResult]:
    return [PermissionResult(id=permission.id, name=permission.name) for permission in permissions]


def to_role_permission_result(
    role_permission: RolePermission,
    permission_names: dict[str, str],
) -> RolePermissionResult:
    return RolePermissionResult(
        id=role_permission.permission_id,
        name=permission_names.get(role_permission.permission_id, role_permission.permission_id),
        scope=role_permission.scope,
    )


def to_role_result(
    role: Role,
    role_permissions: list[RolePermission],
    permission_names: dict[str, str],
) -> RoleResult:
    return RoleResult(
        id=role.id,
        name=role.name,
        permissions=[
            to_role_permission_result(role_permission, permission_names) for role_permission in role_permissions
        ],
    )
