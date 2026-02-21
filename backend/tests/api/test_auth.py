from http import HTTPStatus

import pytest
from starlette.testclient import TestClient


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
