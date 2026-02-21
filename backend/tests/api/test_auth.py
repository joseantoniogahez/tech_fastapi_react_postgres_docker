from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import jwt
import pytest
from starlette.testclient import TestClient

from app.const.settings import AuthSettings


def _build_access_token(username: str) -> str:
    settings = AuthSettings()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire_at}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


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
    assert response.json() == {"detail": "Invalid username or password"}
    assert response.headers["www-authenticate"] == "Bearer"


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
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_current_active_user_when_user_does_not_exist(mock_client: TestClient) -> None:
    token = _build_access_token("ghost-user")

    response = mock_client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_get_current_active_user_when_user_is_disabled(mock_client: TestClient) -> None:
    token_response = mock_client.post(
        "/token",
        data={
            "username": "disabled_user",
            "password": "admin123",
        },
    )
    access_token = token_response.json()["access_token"]

    response = mock_client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": "Inactive user"}
