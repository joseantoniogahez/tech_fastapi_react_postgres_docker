from typing import Annotated, Any

from fastapi import Body, status

from app.openapi.common import INTERNAL_ERROR_EXAMPLE, build_error_response
from app.schemas.api.auth import RegisterUser, UpdateCurrentUser

TOKEN_RESPONSE_EXAMPLE: dict[str, Any] = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
}

AUTHENTICATED_USER_EXAMPLE: dict[str, Any] = {
    "id": 1,
    "username": "admin",
    "disabled": False,
}

REGISTER_USER_BODY_EXAMPLES: dict[str, Any] = {
    "new_user": {
        "summary": "Valid registration",
        "value": {
            "username": "new_user",
            "password": "StrongPass1",
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
            "current_password": "OldPass1",
            "new_password": "NewPass2",
        },
    },
    "both": {
        "summary": "Change username and password",
        "value": {
            "username": "new_username",
            "current_password": "OldPass1",
            "new_password": "NewPass2",
        },
    },
}

RegisterUserPayload = Annotated[
    RegisterUser,
    Body(
        description="New user registration payload.",
        examples=REGISTER_USER_BODY_EXAMPLES,
    ),
]

UpdateCurrentUserPayload = Annotated[
    UpdateCurrentUser,
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
                        "username": "admin",
                        "password": "admin123",
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
