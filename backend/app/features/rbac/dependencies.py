from typing import Annotated

from fastapi import Depends

from app.core.authorization import PermissionId, PermissionScope
from app.core.authorization.dependencies import require_authorized_user
from app.features.auth.principal import CurrentPrincipal

RBAC_PERMISSION_IDS: dict[str, str] = {
    "roles": PermissionId.ROLE_MANAGE,
    "role_permissions": PermissionId.ROLE_PERMISSION_MANAGE,
    "user_roles": PermissionId.USER_ROLE_MANAGE,
    "users": PermissionId.USER_MANAGE,
}

RBACRoleAdminAuth = Annotated[
    CurrentPrincipal,
    Depends(require_authorized_user(RBAC_PERMISSION_IDS["roles"], required_scope=PermissionScope.ANY)),
]
RBACRolePermissionAdminAuth = Annotated[
    CurrentPrincipal,
    Depends(require_authorized_user(RBAC_PERMISSION_IDS["role_permissions"], required_scope=PermissionScope.ANY)),
]
RBACUserRoleAdminAuth = Annotated[
    CurrentPrincipal,
    Depends(require_authorized_user(RBAC_PERMISSION_IDS["user_roles"], required_scope=PermissionScope.ANY)),
]
RBACUserAdminAuth = Annotated[
    CurrentPrincipal,
    Depends(require_authorized_user(RBAC_PERMISSION_IDS["users"], required_scope=PermissionScope.ANY)),
]
