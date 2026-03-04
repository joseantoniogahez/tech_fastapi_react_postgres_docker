import hashlib
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any

import jwt
import pytest
from starlette.testclient import TestClient

from app.const.settings import AuthSettings
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
        "/token",
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


@pytest.mark.parametrize(
    "credentials",
    [
        {"username": "admin", "password": "wrong-password"},
        {"username": "unknown", "password": "admin123"},
    ],
)
def test_token_invalid_credentials(mock_client: TestClient, credentials: dict[str, str]) -> None:
    response = mock_client.post("/token", data=credentials)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    _assert_error_payload(response, "unauthorized", "Invalid username or password")
    assert response.headers["www-authenticate"] == "Bearer"


def test_token_disabled_user(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/token",
        data={
            "username": "disabled_user",
            "password": "admin123",
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    _assert_error_payload(response, "forbidden", "Inactive user")


def test_get_current_active_user(mock_client: TestClient) -> None:
    token_response = mock_client.post(
        "/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    access_token = token_response.json()["access_token"]

    response = mock_client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": 1,
        "username": "admin",
        "disabled": False,
    }


def test_get_current_active_user_with_invalid_token(mock_client: TestClient) -> None:
    response = mock_client.get("/users/me", headers={"Authorization": "Bearer not-a-valid-token"})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    _assert_error_payload(response, "unauthorized", "Could not validate credentials")
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_current_active_user_when_user_does_not_exist(mock_client: TestClient) -> None:
    token = _build_access_token("ghost-user")

    response = mock_client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    _assert_error_payload(response, "unauthorized", "Could not validate credentials")
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_current_active_user_when_user_is_disabled(mock_client: TestClient) -> None:
    token = _build_access_token("disabled_user")
    response = mock_client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == HTTPStatus.FORBIDDEN
    _assert_error_payload(response, "forbidden", "Inactive user")


def test_register_user_success(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/users/register",
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
        "/token",
        data={
            "username": "NEW_USER",
            "password": "StrongPass1",
        },
    )
    assert token_response.status_code == HTTPStatus.OK


def test_register_user_invalid_username_format(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/users/register",
        json={
            "username": "invalid user!",
            "password": "StrongPass1",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(
        response,
        "invalid_input",
        "Username has invalid format",
        details={"allowed": "lowercase letters, numbers, dot, underscore and hyphen"},
    )


def test_register_user_username_conflict(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/users/register",
        json={
            "username": "admin",
            "password": "StrongPass1",
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    _assert_error_payload(
        response,
        "conflict",
        "Username already exists",
        details={"username": "admin"},
    )


def test_register_user_password_policy(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/users/register",
        json={
            "username": "policy_user",
            "password": "onlylowercase1",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(
        response,
        "invalid_input",
        "Password does not meet policy",
        details={"violations": ["Password must include at least one uppercase letter"]},
    )


@pytest.mark.parametrize(
    ("password", "expected_violations"),
    [
        ("ONLYUPPER1", ["Password must include at least one lowercase letter"]),
        ("NoDigitsPass", ["Password must include at least one number"]),
        ("Xpolicy_user9", ["Password cannot contain the username"]),
    ],
)
def test_register_user_password_policy_additional_violations(
    mock_client: TestClient,
    password: str,
    expected_violations: list[str],
) -> None:
    response = mock_client.post(
        "/users/register",
        json={
            "username": "policy_user",
            "password": password,
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(
        response,
        "invalid_input",
        "Password does not meet policy",
        details={"violations": expected_violations},
    )


def test_update_current_user_username_and_password(mock_client: TestClient) -> None:
    register_response = mock_client.post(
        "/users/register",
        json={
            "username": "profile_user",
            "password": "ProfilePass1",
        },
    )
    assert register_response.status_code == HTTPStatus.CREATED
    user_id = register_response.json()["id"]

    login_response = mock_client.post(
        "/token",
        data={
            "username": "profile_user",
            "password": "ProfilePass1",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    update_response = mock_client.patch(
        "/users/me",
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
        "/token",
        data={
            "username": "profile_user",
            "password": "ProfilePass1",
        },
    )
    assert old_login.status_code == HTTPStatus.UNAUTHORIZED

    new_login = mock_client.post(
        "/token",
        data={
            "username": "PROFILE_USER_V2",
            "password": "ProfilePass2",
        },
    )
    assert new_login.status_code == HTTPStatus.OK


def test_update_current_user_requires_current_password(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/users/me",
        headers=headers,
        json={"new_password": "AdminPass9"},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(response, "invalid_input", "current_password is required to update password")


def test_update_current_user_requires_new_password(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/users/me",
        headers=headers,
        json={"current_password": "admin123"},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(response, "invalid_input", "new_password is required when current_password is provided")


def test_update_current_user_requires_at_least_one_field(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/users/me",
        headers=headers,
        json={},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(response, "invalid_input", "At least one field must be provided to update the user")


def test_update_current_user_same_username_has_no_changes(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/users/me",
        headers=headers,
        json={"username": " ADMIN "},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(response, "invalid_input", "No changes detected")


def test_update_current_user_rejects_invalid_current_password(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/users/me",
        headers=headers,
        json={
            "current_password": "wrong-password",
            "new_password": "AdminPass9",
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    _assert_error_payload(response, "unauthorized", "Current password is invalid")
    assert response.headers["www-authenticate"] == "Bearer"


def test_update_current_user_rejects_same_password(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/token",
        data={
            "username": "admin",
            "password": "admin123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/users/me",
        headers=headers,
        json={
            "current_password": "admin123",
            "new_password": "admin123",
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    _assert_error_payload(response, "invalid_input", "New password must be different from current password")


def test_update_current_user_username_conflict(mock_client: TestClient) -> None:
    login_response = mock_client.post(
        "/token",
        data={
            "username": "reader_user",
            "password": "reader123",
        },
    )
    assert login_response.status_code == HTTPStatus.OK
    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    response = mock_client.patch(
        "/users/me",
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
