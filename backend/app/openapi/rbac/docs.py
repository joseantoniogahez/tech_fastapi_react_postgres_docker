from typing import Any

from fastapi import status

from app.authorization import PermissionId, PermissionScope
from app.openapi.common import INTERNAL_ERROR_EXAMPLE, build_error_response

PERMISSION_EXAMPLE: dict[str, Any] = {
    "id": PermissionId.BOOK_CREATE,
    "name": "Create books",
}

ROLE_EXAMPLE: dict[str, Any] = {
    "id": 1,
    "name": "admin_role",
    "permissions": [
        {
            "id": PermissionId.BOOK_CREATE,
            "name": "Create books",
            "scope": PermissionScope.ANY,
        },
        {
            "id": PermissionId.ROLE_MANAGE,
            "name": "Manage roles",
            "scope": PermissionScope.ANY,
        },
    ],
}

ROLE_PERMISSION_EXAMPLE: dict[str, Any] = {
    "id": PermissionId.BOOK_UPDATE,
    "name": "Update books",
    "scope": PermissionScope.TENANT,
}

USER_ROLE_ASSIGNMENT_EXAMPLE: dict[str, Any] = {
    "user_id": 3,
    "role_id": 2,
}


def _unauthorized_response() -> dict[str, Any]:
    return build_error_response(
        description="Missing, expired, or invalid token.",
        example={
            "detail": "Could not validate credentials",
            "status": 401,
            "code": "unauthorized",
        },
        include_www_authenticate=True,
    )


def _forbidden_response(permission_id: str, description: str) -> dict[str, Any]:
    return build_error_response(
        description=description,
        example={
            "detail": f"Missing required permission: {permission_id}",
            "status": 403,
            "code": "forbidden",
            "meta": {"permission_id": permission_id},
        },
    )


GET_ROLES_DOC: dict[str, Any] = {
    "summary": "List roles",
    "description": f"List all roles and their permission grants. Requires `{PermissionId.ROLE_MANAGE}`.",
    "response_description": "Roles ordered by name.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Roles fetched successfully.",
            "content": {"application/json": {"example": [ROLE_EXAMPLE]}},
        },
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.ROLE_MANAGE,
            "User lacks permission to read roles.",
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

GET_PERMISSIONS_DOC: dict[str, Any] = {
    "summary": "List permissions",
    "description": (
        f"List the permission catalog available for role assignment. Requires `{PermissionId.ROLE_PERMISSION_MANAGE}`."
    ),
    "response_description": "Permission catalog ordered by ID.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Permissions fetched successfully.",
            "content": {"application/json": {"example": [PERMISSION_EXAMPLE]}},
        },
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.ROLE_PERMISSION_MANAGE,
            "User lacks permission to read role permissions.",
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

CREATE_ROLE_DOC: dict[str, Any] = {
    "status_code": status.HTTP_201_CREATED,
    "summary": "Create role",
    "description": f"Create a role. Requires `{PermissionId.ROLE_MANAGE}`.",
    "response_description": "Created role.",
    "responses": {
        status.HTTP_201_CREATED: {
            "description": "Role created successfully.",
            "content": {"application/json": {"example": ROLE_EXAMPLE}},
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid payload.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["body", "name"], "msg": "Field required"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.ROLE_MANAGE,
            "User lacks permission to create roles.",
        ),
        status.HTTP_409_CONFLICT: build_error_response(
            description="Role name already exists.",
            example={
                "detail": "Role name already exists",
                "status": 409,
                "code": "conflict",
                "meta": {"name": "catalog_editor"},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

UPDATE_ROLE_DOC: dict[str, Any] = {
    "summary": "Rename role",
    "description": f"Rename an existing role. Requires `{PermissionId.ROLE_MANAGE}`.",
    "response_description": "Updated role.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Role updated successfully.",
            "content": {"application/json": {"example": ROLE_EXAMPLE}},
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid path or payload.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["path", "role_id"], "msg": "Input should be greater than or equal to 1"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.ROLE_MANAGE,
            "User lacks permission to update roles.",
        ),
        status.HTTP_404_NOT_FOUND: build_error_response(
            description="Role does not exist.",
            example={
                "detail": "Role 999 not found",
                "status": 404,
                "code": "not_found",
                "meta": {"id": 999},
            },
        ),
        status.HTTP_409_CONFLICT: build_error_response(
            description="Role name already exists.",
            example={
                "detail": "Role name already exists",
                "status": 409,
                "code": "conflict",
                "meta": {"name": "admin_role"},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

DELETE_ROLE_DOC: dict[str, Any] = {
    "status_code": status.HTTP_204_NO_CONTENT,
    "summary": "Delete role",
    "description": (
        "Delete a role and remove its role-permission and user-role assignments. "
        f"Requires `{PermissionId.ROLE_MANAGE}`."
    ),
    "response_description": "Role deleted.",
    "responses": {
        status.HTTP_204_NO_CONTENT: {
            "description": "Role deleted successfully.",
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid role ID.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["path", "role_id"], "msg": "Input should be greater than or equal to 1"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.ROLE_MANAGE,
            "User lacks permission to delete roles.",
        ),
        status.HTTP_404_NOT_FOUND: build_error_response(
            description="Role does not exist.",
            example={
                "detail": "Role 999 not found",
                "status": 404,
                "code": "not_found",
                "meta": {"id": 999},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

UPSERT_ROLE_PERMISSION_DOC: dict[str, Any] = {
    "summary": "Assign role permission",
    "description": f"Assign or update a permission grant on a role. Requires `{PermissionId.ROLE_PERMISSION_MANAGE}`.",
    "response_description": "Assigned role permission.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Role permission assigned successfully.",
            "content": {"application/json": {"example": ROLE_PERMISSION_EXAMPLE}},
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid role ID, permission ID, or scope.",
            example={
                "detail": "Invalid permission scope 'regional'. Expected one of ['any', 'own', 'tenant'].",
                "status": 400,
                "code": "invalid_input",
            },
        ),
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.ROLE_PERMISSION_MANAGE,
            "User lacks permission to manage role permissions.",
        ),
        status.HTTP_404_NOT_FOUND: build_error_response(
            description="Role or permission does not exist.",
            example={
                "detail": f"Permission {PermissionId.BOOK_CREATE} not found",
                "status": 404,
                "code": "not_found",
                "meta": {"permission_id": PermissionId.BOOK_CREATE},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

DELETE_ROLE_PERMISSION_DOC: dict[str, Any] = {
    "status_code": status.HTTP_204_NO_CONTENT,
    "summary": "Remove role permission",
    "description": f"Remove a permission grant from a role. Requires `{PermissionId.ROLE_PERMISSION_MANAGE}`.",
    "response_description": "Role permission removed.",
    "responses": {
        status.HTTP_204_NO_CONTENT: {
            "description": "Role permission removed (or was already absent).",
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid role ID or permission ID.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["path", "permission_id"], "msg": "String should match pattern"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.ROLE_PERMISSION_MANAGE,
            "User lacks permission to manage role permissions.",
        ),
        status.HTTP_404_NOT_FOUND: build_error_response(
            description="Role or permission does not exist.",
            example={
                "detail": "Role 999 not found",
                "status": 404,
                "code": "not_found",
                "meta": {"id": 999},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

ASSIGN_USER_ROLE_DOC: dict[str, Any] = {
    "summary": "Assign user role",
    "description": f"Assign a role to a user. Requires `{PermissionId.USER_ROLE_MANAGE}`.",
    "response_description": "User-role assignment.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Role assigned to user successfully.",
            "content": {"application/json": {"example": USER_ROLE_ASSIGNMENT_EXAMPLE}},
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid user ID or role ID.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["path", "user_id"], "msg": "Input should be greater than or equal to 1"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.USER_ROLE_MANAGE,
            "User lacks permission to manage user role assignments.",
        ),
        status.HTTP_404_NOT_FOUND: build_error_response(
            description="User or role does not exist.",
            example={
                "detail": "User 999 not found",
                "status": 404,
                "code": "not_found",
                "meta": {"id": 999},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

REMOVE_USER_ROLE_DOC: dict[str, Any] = {
    "status_code": status.HTTP_204_NO_CONTENT,
    "summary": "Remove user role",
    "description": f"Remove a role from a user. Requires `{PermissionId.USER_ROLE_MANAGE}`.",
    "response_description": "User-role assignment removed.",
    "responses": {
        status.HTTP_204_NO_CONTENT: {
            "description": "Role removed from user (or was already absent).",
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid user ID or role ID.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["path", "role_id"], "msg": "Input should be greater than or equal to 1"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: _unauthorized_response(),
        status.HTTP_403_FORBIDDEN: _forbidden_response(
            PermissionId.USER_ROLE_MANAGE,
            "User lacks permission to manage user role assignments.",
        ),
        status.HTTP_404_NOT_FOUND: build_error_response(
            description="User or role does not exist.",
            example={
                "detail": "Role 999 not found",
                "status": 404,
                "code": "not_found",
                "meta": {"id": 999},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}
