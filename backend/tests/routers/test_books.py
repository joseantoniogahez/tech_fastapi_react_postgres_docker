from http import HTTPStatus

from starlette.testclient import TestClient

from app.common.pagination import MAX_LIST_LIMIT


def _auth_headers(mock_client: TestClient, username: str = "admin", password: str = "admin123") -> dict[str, str]:
    response = mock_client.post("/token", data={"username": username, "password": password})
    assert response.status_code == HTTPStatus.OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_books(mock_client: TestClient):
    response = mock_client.get("/books")
    assert response.status_code == HTTPStatus.OK

    json_response = response.json()
    assert isinstance(json_response, list)
    assert len(json_response) == 4

    for book in json_response:
        assert isinstance(book, dict)
        assert set(book.keys()) == {"id", "title", "year", "status", "author"}
        assert isinstance(book["author"], dict)
        assert set(book["author"].keys()) == {"id", "name"}
        assert "id" in book
        assert "title" in book


def test_get_books_by_author(mock_client: TestClient):
    response = mock_client.get("/books?author_id=1")
    assert response.status_code == HTTPStatus.OK

    json_response = response.json()
    assert isinstance(json_response, list)

    for book in json_response:
        assert isinstance(book, dict)
        assert set(book.keys()) == {"id", "title", "year", "status", "author"}
        assert isinstance(book["author"], dict)
        assert set(book["author"].keys()) == {"id", "name"}
        assert book["author"]["id"] == 1


def test_get_books_supports_pagination_and_sort(mock_client: TestClient) -> None:
    full_response = mock_client.get(f"/books?sort=-year&limit={MAX_LIST_LIMIT}")
    assert full_response.status_code == HTTPStatus.OK
    full_books = full_response.json()

    paged_response = mock_client.get("/books?sort=-year&offset=1&limit=2")
    assert paged_response.status_code == HTTPStatus.OK
    paged_books = paged_response.json()

    assert paged_books == full_books[1:3]
    assert len(paged_books) == 2


def test_get_books_rejects_limit_over_max(mock_client: TestClient) -> None:
    response = mock_client.get(f"/books?limit={MAX_LIST_LIMIT + 1}")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["code"] == "invalid_input"


def test_get_books_rejects_unknown_sort_field(mock_client: TestClient) -> None:
    response = mock_client.get("/books?sort=author")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["code"] == "invalid_input"


def test_get_published_books(mock_client: TestClient):
    response = mock_client.get("/books/published")
    assert response.status_code == HTTPStatus.OK

    json_response = response.json()
    assert isinstance(json_response, list)
    assert len(json_response) == 3
    assert all(book["status"] == "published" for book in json_response)


def test_get_book_by_id(mock_client: TestClient):
    response = mock_client.get("/books/1")
    assert response.status_code == HTTPStatus.OK

    json_response = response.json()
    assert isinstance(json_response, dict)
    assert set(json_response.keys()) == {"id", "title", "year", "status", "author"}
    assert json_response["id"] == 1
    assert json_response["title"] == "Foundation"
    assert json_response["status"] == "published"


def test_get_book_by_id_not_found(mock_client: TestClient):
    response = mock_client.get("/books/999")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "detail": "Book 999 not found",
        "status": HTTPStatus.NOT_FOUND,
        "code": "not_found",
        "meta": {"book_id": 999},
    }


def test_create_book(mock_client: TestClient):
    book_data = {
        "title": "I, Robot",
        "year": 1950,
        "status": "published",
        "author_id": 1,
        "author_name": "Isaac Asimov",
    }

    response = mock_client.post("/books", json=book_data, headers=_auth_headers(mock_client))
    assert response.status_code == HTTPStatus.CREATED

    json_response = response.json()
    assert isinstance(json_response, dict)
    assert set(json_response.keys()) == {"id", "title", "year", "status", "author"}
    assert isinstance(json_response["author"], dict)
    assert set(json_response["author"].keys()) == {"id", "name"}
    assert json_response["title"] == book_data["title"]
    assert json_response["year"] == book_data["year"]
    assert json_response["status"] == book_data["status"]
    assert json_response["author"]["id"] == book_data["author_id"]
    assert json_response["author"]["name"] == book_data["author_name"]


def test_update_book(mock_client: TestClient):
    book_data = {
        "title": "Foundation",
        "year": 1951,
        "status": "published",
        "author_name": "Isaak Yúdovich Ozímov",
    }

    response = mock_client.put("/books/1", json=book_data, headers=_auth_headers(mock_client))
    assert response.status_code == HTTPStatus.OK

    json_response = response.json()
    assert isinstance(json_response, dict)
    assert set(json_response.keys()) == {"id", "title", "year", "status", "author"}
    assert isinstance(json_response["author"], dict)
    assert set(json_response["author"].keys()) == {"id", "name"}
    assert json_response["title"] == book_data["title"]
    assert json_response["year"] == book_data["year"]
    assert json_response["status"] == book_data["status"]
    assert json_response["author"]["name"] == book_data["author_name"]


def test_update_book_not_found(mock_client: TestClient):
    book_data = {
        "title": "Unknown",
        "year": 2000,
        "status": "draft",
        "author_name": "Unknown Author",
    }

    response = mock_client.put("/books/999", json=book_data, headers=_auth_headers(mock_client))
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "detail": "Book 999 not found",
        "status": HTTPStatus.NOT_FOUND,
        "code": "not_found",
        "meta": {"book_id": 999},
    }


def test_delete_book(mock_client: TestClient):
    response = mock_client.delete("/books/1", headers=_auth_headers(mock_client))
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""


def test_delete_book_not_found_is_noop(mock_client: TestClient):
    response = mock_client.delete("/books/999", headers=_auth_headers(mock_client))
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
