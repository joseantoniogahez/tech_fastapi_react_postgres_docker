from app.schemas.api.rbac import (
    CreateRoleRequest,
    RBACPermission,
    RBACRole,
    RBACRolePermission,
    SetRolePermissionRequest,
    UpdateRoleRequest,
    UserRoleAssignmentResponse,
)
from app.schemas.application.rbac import (
    CreateRoleCommand,
    PermissionResult,
    RolePermissionResult,
    RoleResult,
    SetRolePermissionCommand,
    UpdateRoleCommand,
    UserRoleAssignmentResult,
)


def to_create_role_command(role_data: CreateRoleRequest) -> CreateRoleCommand:
    return CreateRoleCommand.from_api(role_data)


def to_update_role_command(role_data: UpdateRoleRequest) -> UpdateRoleCommand:
    return UpdateRoleCommand.from_api(role_data)


def to_set_role_permission_command(
    assignment: SetRolePermissionRequest,
) -> SetRolePermissionCommand:
    return SetRolePermissionCommand.from_api(assignment)


def to_permission_response(permission: PermissionResult) -> RBACPermission:
    return RBACPermission.from_application(permission)


def to_permission_response_list(permissions: list[PermissionResult]) -> list[RBACPermission]:
    return [to_permission_response(permission) for permission in permissions]


def to_role_permission_response(permission: RolePermissionResult) -> RBACRolePermission:
    return RBACRolePermission.from_application(permission)


def to_role_response(role: RoleResult) -> RBACRole:
    return RBACRole.from_application(role)


def to_role_response_list(roles: list[RoleResult]) -> list[RBACRole]:
    return [to_role_response(role) for role in roles]


def to_user_role_assignment_response(
    assignment: UserRoleAssignmentResult,
) -> UserRoleAssignmentResponse:
    return UserRoleAssignmentResponse.from_application(assignment)
