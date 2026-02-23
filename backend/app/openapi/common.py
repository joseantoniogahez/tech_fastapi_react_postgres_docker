from typing import Any

ERROR_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["detail", "status", "code"],
    "properties": {
        "detail": {"type": "string", "description": "Human-readable error message."},
        "status": {"type": "integer", "description": "HTTP status code."},
        "code": {"type": "string", "description": "Machine-readable domain error code."},
        "meta": {"description": "Optional structured error metadata."},
    },
}

WWW_AUTHENTICATE_HEADER: dict[str, Any] = {
    "WWW-Authenticate": {
        "description": "Bearer authentication challenge.",
        "schema": {"type": "string", "example": "Bearer"},
    }
}

INTERNAL_ERROR_EXAMPLE: dict[str, Any] = {
    "detail": "Internal server error",
    "status": 500,
    "code": "internal_error",
}


def build_error_response(
    *,
    description: str,
    example: dict[str, Any],
    include_www_authenticate: bool = False,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "description": description,
        "content": {
            "application/json": {
                "schema": ERROR_RESPONSE_SCHEMA,
                "example": example,
            }
        },
    }
    if include_www_authenticate:
        response["headers"] = WWW_AUTHENTICATE_HEADER
    return response


__all__ = [
    "ERROR_RESPONSE_SCHEMA",
    "WWW_AUTHENTICATE_HEADER",
    "INTERNAL_ERROR_EXAMPLE",
    "build_error_response",
]
