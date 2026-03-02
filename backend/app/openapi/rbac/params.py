from typing import Annotated

from fastapi import Body, Path

from app.authorization import PERMISSION_ID_PATTERN, PermissionId, PermissionScope
from app.schemas.rbac import CreateRole, SetRolePermission, UpdateRole

RoleIdPath = Annotated[
    int,
    Path(
        ge=1,
        description="Role ID.",
        examples=[1],
    ),
]

UserIdPath = Annotated[
    int,
    Path(
        ge=1,
        description="User ID.",
        examples=[1],
    ),
]

PermissionIdPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=100,
        pattern=PERMISSION_ID_PATTERN.pattern,
        description="Permission ID in `<resource>:<action>` format.",
        examples=[PermissionId.BOOK_CREATE],
    ),
]

CreateRolePayload = Annotated[
    CreateRole,
    Body(
        description="Payload to create a role.",
        examples={
            "default": {
                "summary": "Create a new role",
                "value": {"name": "catalog_editor"},
            }
        },
    ),
]

UpdateRolePayload = Annotated[
    UpdateRole,
    Body(
        description="Payload to rename a role.",
        examples={
            "default": {
                "summary": "Rename an existing role",
                "value": {"name": "catalog_manager"},
            }
        },
    ),
]

SetRolePermissionPayload = Annotated[
    SetRolePermission,
    Body(
        description="Assign or update a permission grant on a role.",
        examples={
            "default": {
                "summary": "Grant tenant-scoped access",
                "value": {"scope": PermissionScope.TENANT},
            }
        },
    ),
]
