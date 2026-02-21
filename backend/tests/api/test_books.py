from http import HTTPStatus

from starlette.testclient import TestClient


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


def test_add_book(mock_client: TestClient):
    book_data = {
        "title": "I, Robot",
        "year": 1950,
        "status": "published",
        "author_id": 1,
        "author_name": "Isaac Asimov",
    }

    response = mock_client.post("/books", json=book_data, headers=_auth_headers(mock_client))
    assert response.status_code == HTTPStatus.OK

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
        "id": 1,
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


def test_delete_book(mock_client: TestClient):
    response = mock_client.delete("/books/1", headers=_auth_headers(mock_client))
    assert response.status_code == HTTPStatus.OK
    assert response.text == "null"
