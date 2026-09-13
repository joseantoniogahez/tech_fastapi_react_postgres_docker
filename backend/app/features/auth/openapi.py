from typing import Annotated, Any

from fastapi import Body, status

from app.core.common.openapi import INTERNAL_ERROR_EXAMPLE, build_error_response
from app.core.rate_limit import (
    RATE_LIMIT_HEADER,
    RATE_LIMIT_REMAINING_HEADER,
    RATE_LIMIT_RESET_HEADER,
    RETRY_AFTER_HEADER,
)
from app.features.auth.schemas import RegisterUserRequest, UpdateCurrentUserRequest

TOKEN_RESPONSE_EXAMPLE: dict[str, Any] = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
}

QUOTA_RESPONSE_HEADERS: dict[str, Any] = {
    RATE_LIMIT_HEADER: {
        "description": "Maximum requests allowed in the fixed window.",
        "schema": {"type": "integer", "minimum": 1},
    },
    RATE_LIMIT_REMAINING_HEADER: {
        "description": "Requests remaining in the current fixed window.",
        "schema": {"type": "integer", "minimum": 0},
    },
    RATE_LIMIT_RESET_HEADER: {
        "description": "Whole seconds until the current fixed window resets.",
        "schema": {"type": "integer", "minimum": 1},
    },
}

RATE_LIMITED_RESPONSE_HEADERS: dict[str, Any] = {
    **QUOTA_RESPONSE_HEADERS,
    RETRY_AFTER_HEADER: {
        "description": "Whole seconds to wait before retrying.",
        "schema": {"type": "integer", "minimum": 1},
    },
}


def _rate_limit_responses() -> dict[int, dict[str, Any]]:
    return {
        status.HTTP_429_TOO_MANY_REQUESTS: build_error_response(
            description="The authentication surface quota is exhausted.",
            example={
                "detail": "Too many requests. Try again later.",
                "status": 429,
                "code": "rate_limited",
                "meta": {"retry_after_seconds": 60},
            },
            additional_headers=RATE_LIMITED_RESPONSE_HEADERS,
        ),
        status.HTTP_503_SERVICE_UNAVAILABLE: build_error_response(
            description="The required shared rate-limit store is unavailable.",
            example={
                "detail": "Service temporarily unavailable",
                "status": 503,
                "code": "service_unavailable",
                "meta": {"dependency": "rate_limit_store"},
            },
        ),
    }


AUTHENTICATED_USER_EXAMPLE: dict[str, Any] = {
    "id": 1,
    "username": "admin",
    "disabled": False,
    "permissions": [
        "audit_logs:read",
        "role_permissions:manage",
        "roles:manage",
        "user_roles:manage",
        "users:manage",
    ],
}

REGISTER_USER_BODY_EXAMPLES: dict[str, Any] = {
    "new_user": {
        "summary": "Valid registration",
        "value": {
            "username": "new_user",
            "password": "{{strong_password}}",
        },
    }
}

UPDATE_CURRENT_USER_BODY_EXAMPLES: dict[str, Any] = {
    "username": {
        "summary": "Change username",
        "value": {"username": "new_username"},
    },
    "password": {
        "summary": "Change password",
        "value": {
            "current_password": "{{current_password}}",
            "new_password": "{{new_password}}",
        },
    },
    "both": {
        "summary": "Change username and password",
        "value": {
            "username": "new_username",
            "current_password": "{{current_password}}",
            "new_password": "{{new_password}}",
        },
    },
}

RegisterUserPayload = Annotated[
    RegisterUserRequest,
    Body(
        description="New user registration payload.",
        examples=REGISTER_USER_BODY_EXAMPLES,
    ),
]

UpdateCurrentUserPayload = Annotated[
    UpdateCurrentUserRequest,
    Body(
        description="Optional fields to update the authenticated user.",
        examples=UPDATE_CURRENT_USER_BODY_EXAMPLES,
    ),
]

LOGIN_FOR_ACCESS_TOKEN_DOC: dict[str, Any] = {
    "summary": "Get access token",
    "description": "Authenticate a user with `application/x-www-form-urlencoded` and return a JWT bearer token.",
    "response_description": "Valid bearer access token.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Authentication successful.",
            "content": {"application/json": {"example": TOKEN_RESPONSE_EXAMPLE}},
            "headers": QUOTA_RESPONSE_HEADERS,
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid credential input format.",
            example={
                "detail": "Request validation error",
                "status": 400,
                "code": "invalid_input",
                "meta": [{"loc": ["body", "username"], "msg": "Field required"}],
            },
        ),
        status.HTTP_401_UNAUTHORIZED: build_error_response(
            description="Invalid username or password.",
            example={
                "detail": "Invalid username or password",
                "status": 401,
                "code": "unauthorized",
            },
            include_www_authenticate=True,
        ),
        status.HTTP_403_FORBIDDEN: build_error_response(
            description="User is authenticated but inactive.",
            example={
                "detail": "Inactive user",
                "status": 403,
                "code": "forbidden",
            },
        ),
        **_rate_limit_responses(),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
    "openapi_extra": {
        "requestBody": {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "example": {
                        "username": "demo_user",
                        "password": "{{password}}",
                    }
                }
            },
        }
    },
}

REGISTER_USER_DOC: dict[str, Any] = {
    "status_code": status.HTTP_201_CREATED,
    "summary": "Register user",
    "description": (
        "Create a local active user. `username` is normalized to lowercase and the password "
        "must satisfy the service password policy."
    ),
    "response_description": "User created successfully.",
    "responses": {
        status.HTTP_201_CREATED: {
            "description": "User registered.",
            "content": {"application/json": {"example": AUTHENTICATED_USER_EXAMPLE}},
            "headers": QUOTA_RESPONSE_HEADERS,
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid registration input or password policy violation.",
            example={
                "detail": "Password does not meet policy",
                "status": 400,
                "code": "invalid_input",
                "meta": {"violations": ["Password must include at least one uppercase letter"]},
            },
        ),
        status.HTTP_409_CONFLICT: build_error_response(
            description="Username already exists.",
            example={
                "detail": "Username already exists",
                "status": 409,
                "code": "conflict",
                "meta": {"username": "admin"},
            },
        ),
        **_rate_limit_responses(),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

READ_CURRENT_USER_DOC: dict[str, Any] = {
    "summary": "Get current user",
    "description": "Return the user associated with the bearer token in the `Authorization` header.",
    "response_description": "Authenticated user profile.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Authenticated user.",
            "content": {"application/json": {"example": AUTHENTICATED_USER_EXAMPLE}},
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
            description="User is authenticated but inactive.",
            example={
                "detail": "Inactive user",
                "status": 403,
                "code": "forbidden",
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}

UPDATE_CURRENT_USER_DOC: dict[str, Any] = {
    "summary": "Update current user",
    "description": (
        "Update `username`, password, or both. Password change requires both `current_password` and `new_password`."
    ),
    "response_description": "User updated successfully.",
    "responses": {
        status.HTTP_200_OK: {
            "description": "Profile updated.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "profile_user_v2",
                        "disabled": False,
                        "permissions": [],
                    }
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: build_error_response(
            description="Invalid request or no effective changes.",
            example={
                "detail": "At least one field must be provided to update the user",
                "status": 400,
                "code": "invalid_input",
            },
        ),
        status.HTTP_401_UNAUTHORIZED: build_error_response(
            description="Invalid token or incorrect current password.",
            example={
                "detail": "Current password is invalid",
                "status": 401,
                "code": "unauthorized",
            },
            include_www_authenticate=True,
        ),
        status.HTTP_403_FORBIDDEN: build_error_response(
            description="User is authenticated but inactive.",
            example={
                "detail": "Inactive user",
                "status": 403,
                "code": "forbidden",
            },
        ),
        status.HTTP_409_CONFLICT: build_error_response(
            description="New username is already in use.",
            example={
                "detail": "Username already exists",
                "status": 409,
                "code": "conflict",
                "meta": {"username": "admin"},
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: build_error_response(
            description="Unhandled internal server error.",
            example=INTERNAL_ERROR_EXAMPLE,
        ),
    },
}
