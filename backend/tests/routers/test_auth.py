import hashlib
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any

import jwt
from starlette.testclient import TestClient

from app.core.config.settings import AuthSettings
from utils.testing_support.api_assertions import assert_error_response


def _build_access_token(username: str) -> str:
    settings = AuthSettings()
    issued_at = datetime.now(UTC)
    expire_at = issued_at + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(issued_at.timestamp()),
        "exp": int(expire_at.timestamp()),
        "jti": f"test-{username}",
        "rbac_version": hashlib.sha256(b"").hexdigest(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _assert_error_payload(response: Any, error_type: str, message: str, details: Any | None = None) -> None:
    assert_error_response(
        response,
        detail=message,
        status_code=response.status_code,
        code=error_type,
        meta=details,
    )


def test_token_success(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/v1/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert isinstance(payload["access_token"], str)
    assert payload["access_token"]


def test_token_rejects_invalid_credentials_variants(mock_client: TestClient) -> None:
    for credentials in (
        {"username": "admin", "password": "wrong-password"},
        {"username": "unknown", "password": "admin123"},
    ):
        response = mock_client.post("/v1/token", data=credentials)

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        _assert_error_payload(response, "unauthorized", "Invalid username or password")
        assert response.headers["www-authenticate"] == "Bearer"


def test_token_disabled_user(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/v1/token",
        data={
            "username": "disabled_user",
            "password": "admin123",
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    _assert_error_payload(response, "forbidden", "Inactive user")


def test_get_current_active_user(mock_client: TestClient) -> None:
    token_response = mock_client.post(
        "/v1/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    access_token = token_response.json()["access_token"]

    response = mock_client.get("/v1/users/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "username": "admin",
        "disabled": False,
    }


def test_get_current_active_user_rejects_invalid_tokens_and_inactive_user(mock_client: TestClient) -> None:
    authorizations = (
        "Bearer not-a-valid-token",
        f"Bearer {_build_access_token('ghost-user')}",
        f"Bearer {_build_access_token('disabled_user')}",
    )
    status_codes = (HTTPStatus.UNAUTHORIZED, HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)
    error_types = ("unauthorized", "unauthorized", "forbidden")
    messages = ("Could not validate credentials", "Could not validate credentials", "Inactive user")
    expects_www_authenticate_values = (True, True, False)

    for authorization, status_code, error_type, message, expects_www_authenticate in zip(
        authorizations, status_codes, error_types, messages, expects_www_authenticate_values, strict=True
    ):
        response = mock_client.get("/v1/users/me", headers={"Authorization": authorization})

        assert response.status_code == status_code
        error_type = error_type
        _assert_error_payload(response, error_type, message)
        if expects_www_authenticate:
            assert response.headers["www-authenticate"] == "Bearer"


def test_register_user_success(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/v1/users/register",
        json={
            "username": " new_user ",
            "password": "StrongPass1",
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    payload = response.json()
    assert isinstance(payload["id"], int)
    assert payload["username"] == "new_user"
    assert payload["disabled"] is False

    token_response = mock_client.post(
        "/v1/token",
        data={
            "username": "NEW_USER",
            "password": "StrongPass1",
        },
    )
    assert token_response.status_code == HTTPStatus.OK


def test_register_user_rejects_common_error_cases(mock_client: TestClient) -> None:
    payloads = (
        {"username": "invalid user!", "password": "StrongPass1"},
        {"username": "admin", "password": "StrongPass1"},
        {"username": "policy_user", "password": "onlylowercase1"},
    )
    status_codes = (HTTPStatus.BAD_REQUEST, HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST)
    error_types = ("invalid_input", "conflict", "invalid_input")
    messages = ("Username has invalid format", "Username already exists", "Password does not meet policy")
    detail_dicts = (
        {"allowed": "lowercase letters, numbers, dot, underscore and hyphen"},
        {"username": "admin"},
        {"violations": ["Password must include at least one uppercase letter"]},
    )

    for payload, status_code, error_type, message, details in zip(
        payloads, status_codes, error_types, messages, detail_dicts, strict=True
    ):
        response = mock_client.post("/v1/users/register", json=payload)

        assert response.status_code == status_code
        _assert_error_payload(
            response,
            error_type,
            message,
            details=details,
        )


def test_update_current_user_username_and_password(mock_client: TestClient) -> None:
    register_response = mock_client.post(
        "/v1/users/register",
        json={
            "username": "profile_user",
            "password": "ProfilePass1",
        },
    )
    assert register_response.status_code == HTTPStatus.CREATED
    user_id = register_response.json()["id"]

    login_response = mock_client.post(
        "/v1/token",
        data={
            "username": "profile_user",
            "password": "ProfilePass1",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    update_response = mock_client.patch(
        "/v1/users/me",
        headers=headers,
        json={
            "username": " profile_user_v2 ",
            "current_password": "ProfilePass1",
            "new_password": "ProfilePass2",
        },
    )

    assert update_response.status_code == HTTPStatus.OK
    assert update_response.json() == {
        "id": user_id,
        "username": "profile_user_v2",
        "disabled": False,
    }

    old_login = mock_client.post(
        "/v1/token",
        data={
            "username": "profile_user",
            "password": "ProfilePass1",
        },
    )
    assert old_login.status_code == HTTPStatus.UNAUTHORIZED

    new_login = mock_client.post(
        "/v1/token",
        data={
            "username": "PROFILE_USER_V2",
            "password": "ProfilePass2",
        },
    )
    assert new_login.status_code == HTTPStatus.OK


def test_update_current_user_rejects_invalid_update_payloads(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/v1/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    payloads = (
        {"new_password": "AdminPass9"},
        {"current_password": "admin123"},
        {"username": " ADMIN "},
        {"current_password": "admin123", "new_password": "admin123"},
    )
    expected_messages = (
        "current_password is required to update password",
        "new_password is required when current_password is provided",
        "No changes detected",
        "New password must be different from current password",
    )

    for payload, expected_message in zip(payloads, expected_messages, strict=True):
        response = mock_client.patch("/v1/users/me", headers=headers, json=payload)

        assert response.status_code == HTTPStatus.BAD_REQUEST
        _assert_error_payload(response, "invalid_input", expected_message)

    response = mock_client.patch("/v1/users/me", headers=headers, json={})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(response, "invalid_input", "At least one field must be provided to update the user")


def test_update_current_user_rejects_invalid_current_password(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/v1/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/v1/users/me",
        headers=headers,
        json={
            "current_password": "wrong-password",
            "new_password": "AdminPass9",
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    _assert_error_payload(response, "unauthorized", "Current password is invalid")
    assert response.headers["www-authenticate"] == "Bearer"


def test_update_current_user_username_conflict(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/v1/token",
        data={
            "username": "reader_user",
            "password": "reader123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/v1/users/me",
        headers=headers,
        json={"username": "admin"},
    )

    assert response.status_code == HTTPStatus.CONFLICT
    _assert_error_payload(
        response,
        "conflict",
        "Username already exists",
        details={"username": "admin"},
    )
