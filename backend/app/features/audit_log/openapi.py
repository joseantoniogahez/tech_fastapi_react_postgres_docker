from typing import Any

from fastapi import status

from app.core.authorization import PermissionId
from app.core.common.openapi import INTERNAL_ERROR_EXAMPLE, build_error_response

GET_AUDIT_LOG_ENTRIES_DOC: dict[str, Any] = {
    "summary": "List audit log entries",
    "description": (
        f"Return the most recent audit log entries for administrator review. Requires `{PermissionId.AUDIT_LOG_READ}`."
    ),
    "response_description": "Most recent audit log entries.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Audit log entries returned.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "actor_user_id": 1,
                            "action": "user.created",
                            "resource_type": "user",
                            "resource_id": "42",
                            "summary": "Created user ops_user",
                            "created_at": "2026-05-01T12:00:00Z",
                        }
                    ]
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: build_error_response(
            description="Missing, expired, or invalid token.",
            example={
                "detail": "Could not validate credentials",
                "status": 401,
                "code": "unauthorized",
            },
            include_www_authenticate=True,
        ),
        status.HTTP_403_FORBIDDEN: build_error_response(
            description="User lacks permission to read audit logs.",
            example={
                "detail": f"Missing required permission: {PermissionId.AUDIT_LOG_READ}",
                "status": 403,
                "code": "forbidden",
                "meta": {"permission_id": PermissionId.AUDIT_LOG_READ},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}
