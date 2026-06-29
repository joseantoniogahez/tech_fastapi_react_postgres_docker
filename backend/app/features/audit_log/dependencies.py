from typing import Annotated

from fastapi import Depends

from app.core.authorization import PermissionId, PermissionScope
from app.core.authorization.dependencies import require_authorized_user
from app.features.auth.principal import CurrentPrincipal

AuditLogReadAuth = Annotated[
    CurrentPrincipal,
    Depends(require_authorized_user(PermissionId.AUDIT_LOG_READ, required_scope=PermissionScope.ANY)),
]
