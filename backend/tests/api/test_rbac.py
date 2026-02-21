from http import HTTPStatus

from starlette.testclient import TestClient


def _auth_headers(mock_client: TestClient, username: str, password: str) -> dict[str, str]:
    response = mock_client.post("/token", data={"username": username, "password": password})
    assert response.status_code == HTTPStatus.OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_book(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/books",
        json={
            "title": "Pebble in the Sky",
            "year": 1950,
            "status": "published",
            "author_name": "Isaac Asimov",
        },
        headers=_auth_headers(mock_client, "admin", "admin123"),
    )

    assert response.status_code == HTTPStatus.OK


def test_reader_cannot_create_book(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/books",
        json={
            "title": "The Caves of Steel",
            "year": 1953,
            "status": "published",
            "author_name": "Isaac Asimov",
        },
        headers=_auth_headers(mock_client, "reader_user", "reader123"),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {
        "detail": "Missing required permission: books:create",
        "status": HTTPStatus.FORBIDDEN,
        "code": "forbidden",
        "meta": {"permission_id": "books:create"},
    }


def test_reader_cannot_delete_book(mock_client: TestClient) -> None:
    response = mock_client.delete(
        "/books/1",
        headers=_auth_headers(mock_client, "reader_user", "reader123"),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {
        "detail": "Missing required permission: books:delete",
        "status": HTTPStatus.FORBIDDEN,
        "code": "forbidden",
        "meta": {"permission_id": "books:delete"},
    }
