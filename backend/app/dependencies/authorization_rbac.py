from typing import Annotated

from fastapi import Depends

from app.authorization import PermissionId, PermissionScope
from app.models.user import User

from .authorization import require_authorized_user

RBAC_PERMISSION_IDS: dict[str, str] = {
    "roles": PermissionId.ROLE_MANAGE,
    "role_permissions": PermissionId.ROLE_PERMISSION_MANAGE,
    "user_roles": PermissionId.USER_ROLE_MANAGE,
}

RBACRoleAdminAuth = Annotated[
    User,
    Depends(require_authorized_user(RBAC_PERMISSION_IDS["roles"], required_scope=PermissionScope.ANY)),
]
RBACRolePermissionAdminAuth = Annotated[
    User,
    Depends(require_authorized_user(RBAC_PERMISSION_IDS["role_permissions"], required_scope=PermissionScope.ANY)),
]
RBACUserRoleAdminAuth = Annotated[
    User,
    Depends(require_authorized_user(RBAC_PERMISSION_IDS["user_roles"], required_scope=PermissionScope.ANY)),
]
