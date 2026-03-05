from http import HTTPStatus

from starlette.testclient import TestClient

from app.authorization import PermissionId
from utils.testing_support.api_assertions import assert_error_response


def _auth_headers(mock_client: TestClient, username: str, password: str) -> dict[str, str]:
    response = mock_client.post("/v1/token", data={"username": username, "password": password})
    assert response.status_code == HTTPStatus.OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_book(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/v1/books",
        json={
            "title": "Pebble in the Sky",
            "year": 1950,
            "status": "published",
            "author_name": "Isaac Asimov",
        },
        headers=_auth_headers(mock_client, "admin", "admin123"),
    )

    assert response.status_code == HTTPStatus.CREATED


def test_reader_cannot_create_book(mock_client: TestClient) -> None:
    response = mock_client.post(
        "/v1/books",
        json={
            "title": "The Caves of Steel",
            "year": 1953,
            "status": "published",
            "author_name": "Isaac Asimov",
        },
        headers=_auth_headers(mock_client, "reader_user", "reader123"),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.BOOK_CREATE}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.BOOK_CREATE},
    )


def test_reader_cannot_delete_book(mock_client: TestClient) -> None:
    response = mock_client.delete(
        "/v1/books/1",
        headers=_auth_headers(mock_client, "reader_user", "reader123"),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.BOOK_DELETE}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.BOOK_DELETE},
    )


def test_user_inherits_permission_through_role_composition(mock_client: TestClient) -> None:
    admin_headers = _auth_headers(mock_client, "admin", "admin123")

    parent_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "creator_parent"},
        headers=admin_headers,
    )
    assert parent_role_response.status_code == HTTPStatus.CREATED
    parent_role_id = parent_role_response.json()["id"]

    child_role_response = mock_client.post(
        "/v1/rbac/roles",
        json={"name": "creator_child"},
        headers=admin_headers,
    )
    assert child_role_response.status_code == HTTPStatus.CREATED
    child_role_id = child_role_response.json()["id"]

    assign_permission_response = mock_client.put(
        f"/v1/rbac/roles/{parent_role_id}/permissions/{PermissionId.BOOK_CREATE}",
        json={"scope": "any"},
        headers=admin_headers,
    )
    assert assign_permission_response.status_code == HTTPStatus.OK

    assign_inheritance_response = mock_client.put(
        f"/v1/rbac/roles/{child_role_id}/inherits/{parent_role_id}",
        headers=admin_headers,
    )
    assert assign_inheritance_response.status_code == HTTPStatus.NO_CONTENT

    assign_user_role_response = mock_client.put(
        f"/v1/rbac/users/3/roles/{child_role_id}",
        headers=admin_headers,
    )
    assert assign_user_role_response.status_code == HTTPStatus.OK

    response = mock_client.post(
        "/v1/books",
        json={
            "title": "The Naked Sun",
            "year": 1957,
            "status": "published",
            "author_name": "Isaac Asimov",
        },
        headers=_auth_headers(mock_client, "reader_user", "reader123"),
    )

    assert response.status_code == HTTPStatus.CREATED
