from fastapi import APIRouter

from app.core.setup.dependencies import RBACServiceDependency
from app.features.rbac.dependencies import RBACRoleAdminAuth, RBACRolePermissionAdminAuth, RBACUserRoleAdminAuth
from app.features.rbac.openapi import (
    ASSIGN_USER_ROLE_DOC,
    CREATE_ROLE_DOC,
    DELETE_ROLE_DOC,
    DELETE_ROLE_INHERITANCE_DOC,
    DELETE_ROLE_PERMISSION_DOC,
    GET_PERMISSIONS_DOC,
    GET_ROLES_DOC,
    REMOVE_USER_ROLE_DOC,
    UPDATE_ROLE_DOC,
    UPSERT_ROLE_INHERITANCE_DOC,
    UPSERT_ROLE_PERMISSION_DOC,
    CreateRolePayload,
    ParentRoleIdPath,
    PermissionIdPath,
    RoleIdPath,
    SetRolePermissionPayload,
    UpdateRolePayload,
    UserIdPath,
)
from app.features.rbac.router_mappers import (
    to_create_role_command,
    to_permission_response_list,
    to_role_permission_response,
    to_role_response,
    to_role_response_list,
    to_set_role_permission_command,
    to_update_role_command,
    to_user_role_assignment_response,
)
from app.features.rbac.schemas import RBACPermission, RBACRole, RBACRolePermission, UserRoleAssignmentResponse

router = APIRouter(
    prefix="/rbac",
    tags=["rbac"],
)


@router.get("/roles", response_model=list[RBACRole], **GET_ROLES_DOC)
async def list_roles(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
) -> list[RBACRole]:
    roles = await rbac_service.list_roles()
    return to_role_response_list(roles)


@router.get("/permissions", response_model=list[RBACPermission], **GET_PERMISSIONS_DOC)
async def list_permissions(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRolePermissionAdminAuth,
) -> list[RBACPermission]:
    permissions = await rbac_service.list_permissions()
    return to_permission_response_list(permissions)


@router.post("/roles", response_model=RBACRole, **CREATE_ROLE_DOC)
async def create_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
    role_data: CreateRolePayload,
) -> RBACRole:
    role = await rbac_service.create_role(to_create_role_command(role_data))
    return to_role_response(role)


@router.put("/roles/{role_id}", response_model=RBACRole, **UPDATE_ROLE_DOC)
async def update_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
    role_id: RoleIdPath,
    role_data: UpdateRolePayload,
) -> RBACRole:
    role = await rbac_service.update_role(role_id, to_update_role_command(role_data))
    return to_role_response(role)


@router.delete("/roles/{role_id}", **DELETE_ROLE_DOC)
async def delete_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
    role_id: RoleIdPath,
) -> None:
    await rbac_service.delete_role(role_id)


@router.put(
    "/roles/{role_id}/inherits/{parent_role_id}",
    **UPSERT_ROLE_INHERITANCE_DOC,
)
async def assign_role_inheritance(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
    role_id: RoleIdPath,
    parent_role_id: ParentRoleIdPath,
) -> None:
    await rbac_service.assign_role_inheritance(role_id, parent_role_id)


@router.delete(
    "/roles/{role_id}/inherits/{parent_role_id}",
    **DELETE_ROLE_INHERITANCE_DOC,
)
async def remove_role_inheritance(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
    role_id: RoleIdPath,
    parent_role_id: ParentRoleIdPath,
) -> None:
    await rbac_service.remove_role_inheritance(role_id, parent_role_id)


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
        to_set_role_permission_command(assignment),
    )
    return to_role_permission_response(role_permission)


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
    response_model=UserRoleAssignmentResponse,
    **ASSIGN_USER_ROLE_DOC,
)
async def assign_user_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACUserRoleAdminAuth,
    user_id: UserIdPath,
    role_id: RoleIdPath,
) -> UserRoleAssignmentResponse:
    assignment = await rbac_service.assign_user_role(user_id, role_id)
    return to_user_role_assignment_response(assignment)


@router.delete("/users/{user_id}/roles/{role_id}", **REMOVE_USER_ROLE_DOC)
async def remove_user_role(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACUserRoleAdminAuth,
    user_id: UserIdPath,
    role_id: RoleIdPath,
) -> None:
    await rbac_service.remove_user_role(user_id, role_id)
