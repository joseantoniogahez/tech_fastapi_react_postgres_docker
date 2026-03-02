from fastapi import APIRouter

from app.dependencies.authorization_rbac import RBACRoleAdminAuth, RBACRolePermissionAdminAuth, RBACUserRoleAdminAuth
from app.dependencies.services import RBACServiceDependency
from app.openapi.rbac import (
    ASSIGN_USER_ROLE_DOC,
    CREATE_ROLE_DOC,
    DELETE_ROLE_DOC,
    DELETE_ROLE_PERMISSION_DOC,
    GET_PERMISSIONS_DOC,
    GET_ROLES_DOC,
    REMOVE_USER_ROLE_DOC,
    UPDATE_ROLE_DOC,
    UPSERT_ROLE_PERMISSION_DOC,
    CreateRolePayload,
    PermissionIdPath,
    RoleIdPath,
    SetRolePermissionPayload,
    UpdateRolePayload,
    UserIdPath,
)
from app.schemas.api.rbac import RBACPermission, RBACRole, RBACRolePermission, UserRoleAssignment
from app.schemas.application.rbac import (
    CreateRoleCommand,
    PermissionResult,
    RolePermissionResult,
    RoleResult,
    SetRolePermissionCommand,
    UpdateRoleCommand,
    UserRoleAssignmentResult,
)

router = APIRouter(
    prefix="/rbac",
    tags=["rbac"],
)


def _to_permission_response(permission: PermissionResult) -> RBACPermission:
    return RBACPermission.from_application(permission)


def _to_role_permission_response(permission: RolePermissionResult) -> RBACRolePermission:
    return RBACRolePermission.from_application(permission)


def _to_role_response(role: RoleResult) -> RBACRole:
    return RBACRole.from_application(role)


def _to_user_role_assignment_response(assignment: UserRoleAssignmentResult) -> UserRoleAssignment:
    return UserRoleAssignment.from_application(assignment)


@router.get("/roles", response_model=list[RBACRole], **GET_ROLES_DOC)
async def list_roles(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
) -> list[RBACRole]:
    roles = await rbac_service.list_roles()
    return [_to_role_response(role) for role in roles]


@router.get("/permissions", response_model=list[RBACPermission], **GET_PERMISSIONS_DOC)
async def list_permissions(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRolePermissionAdminAuth,
) -> list[RBACPermission]:
    permissions = await rbac_service.list_permissions()
    return [_to_permission_response(permission) for permission in permissions]


@router.post("/roles", response_model=RBACRole, **CREATE_ROLE_DOC)
async def create_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
    role_data: CreateRolePayload,
) -> RBACRole:
    role = await rbac_service.create_role(CreateRoleCommand.from_api(role_data))
    return _to_role_response(role)


@router.put("/roles/{role_id}", response_model=RBACRole, **UPDATE_ROLE_DOC)
async def update_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
    role_id: RoleIdPath,
    role_data: UpdateRolePayload,
) -> RBACRole:
    role = await rbac_service.update_role(role_id, UpdateRoleCommand.from_api(role_data))
    return _to_role_response(role)


@router.delete("/roles/{role_id}", **DELETE_ROLE_DOC)
async def delete_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
    role_id: RoleIdPath,
) -> None:
    await rbac_service.delete_role(role_id)


@router.put(
    "/roles/{role_id}/permissions/{permission_id}",
    response_model=RBACRolePermission,
    **UPSERT_ROLE_PERMISSION_DOC,
)
async def assign_role_permission(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRolePermissionAdminAuth,
    role_id: RoleIdPath,
    permission_id: PermissionIdPath,
    assignment: SetRolePermissionPayload,
) -> RBACRolePermission:
    role_permission = await rbac_service.assign_role_permission(
        role_id,
        permission_id,
        SetRolePermissionCommand.from_api(assignment),
    )
    return _to_role_permission_response(role_permission)


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    **DELETE_ROLE_PERMISSION_DOC,
)
async def remove_role_permission(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRolePermissionAdminAuth,
    role_id: RoleIdPath,
    permission_id: PermissionIdPath,
) -> None:
    await rbac_service.remove_role_permission(role_id, permission_id)


@router.put(
    "/users/{user_id}/roles/{role_id}",
    response_model=UserRoleAssignment,
    **ASSIGN_USER_ROLE_DOC,
)
async def assign_user_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACUserRoleAdminAuth,
    user_id: UserIdPath,
    role_id: RoleIdPath,
) -> UserRoleAssignment:
    assignment = await rbac_service.assign_user_role(user_id, role_id)
    return _to_user_role_assignment_response(assignment)


@router.delete("/users/{user_id}/roles/{role_id}", **REMOVE_USER_ROLE_DOC)
async def remove_user_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACUserRoleAdminAuth,
    user_id: UserIdPath,
    role_id: RoleIdPath,
) -> None:
    await rbac_service.remove_user_role(user_id, role_id)
