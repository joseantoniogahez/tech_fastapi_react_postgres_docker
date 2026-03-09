from app.features.rbac.schemas import (
    AdminUserResponse,
    AdminUserResult,
    AssignedRole,
    AssignedRoleResult,
    AssignedUser,
    AssignedUserResult,
    CreateAdminUserCommand,
    CreateAdminUserRequest,
    CreateRoleCommand,
    CreateRoleRequest,
    PermissionResult,
    RBACPermission,
    RBACRole,
    RBACRolePermission,
    RolePermissionResult,
    RoleResult,
    SetRolePermissionCommand,
    SetRolePermissionRequest,
    UpdateAdminUserCommand,
    UpdateAdminUserRequest,
    UpdateRoleCommand,
    UpdateRoleRequest,
    UserRoleAssignmentResponse,
    UserRoleAssignmentResult,
)


def to_create_role_command(role_data: CreateRoleRequest) -> CreateRoleCommand:
    return CreateRoleCommand.from_api(role_data)


def to_create_admin_user_command(user_data: CreateAdminUserRequest) -> CreateAdminUserCommand:
    return CreateAdminUserCommand.from_api(user_data)


def to_update_role_command(role_data: UpdateRoleRequest) -> UpdateRoleCommand:
    return UpdateRoleCommand.from_api(role_data)


def to_update_admin_user_command(user_data: UpdateAdminUserRequest) -> UpdateAdminUserCommand:
    return UpdateAdminUserCommand.from_api(user_data)


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


def to_admin_user_response(user: AdminUserResult) -> AdminUserResponse:
    return AdminUserResponse.from_application(user)


def to_admin_user_response_list(users: list[AdminUserResult]) -> list[AdminUserResponse]:
    return [to_admin_user_response(user) for user in users]


def to_assigned_role_response(role: AssignedRoleResult) -> AssignedRole:
    return AssignedRole.from_application(role)


def to_assigned_role_response_list(roles: list[AssignedRoleResult]) -> list[AssignedRole]:
    return [to_assigned_role_response(role) for role in roles]


def to_assigned_user_response(user: AssignedUserResult) -> AssignedUser:
    return AssignedUser.from_application(user)


def to_assigned_user_response_list(users: list[AssignedUserResult]) -> list[AssignedUser]:
    return [to_assigned_user_response(user) for user in users]
