from http import HTTPStatus

from starlette.testclient import TestClient

from app.repositories import MAX_LIST_LIMIT


def test_get_authors(mock_client: TestClient) -> None:
    response = mock_client.get("/authors")
    assert response.status_code == HTTPStatus.OK
    json_response = response.json()
    for author in json_response:
        assert isinstance(author, dict), "Author should be a dictionary."
        assert set(author.keys()) == {
            "id",
            "name",
        }, "Author keys should be {'id', 'name'}."


def test_get_authors_default_sort_is_name_ascending(mock_client: TestClient) -> None:
    response = mock_client.get("/authors")
    assert response.status_code == HTTPStatus.OK

    json_response = response.json()
    names = [author["name"] for author in json_response]
    assert names == sorted(names)


def test_get_authors_supports_pagination_and_sort(mock_client: TestClient) -> None:
    full_response = mock_client.get(f"/authors?sort=-name&limit={MAX_LIST_LIMIT}")
    assert full_response.status_code == HTTPStatus.OK
    full_authors = full_response.json()

    paged_response = mock_client.get("/authors?sort=-name&offset=1&limit=2")
    assert paged_response.status_code == HTTPStatus.OK
    paged_authors = paged_response.json()

    assert paged_authors == full_authors[1:3]
    assert len(paged_authors) == 2


def test_get_authors_rejects_limit_over_max(mock_client: TestClient) -> None:
    response = mock_client.get(f"/authors?limit={MAX_LIST_LIMIT + 1}")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["code"] == "invalid_input"


def test_get_authors_rejects_unknown_sort_field(mock_client: TestClient) -> None:
    response = mock_client.get("/authors?sort=books")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["code"] == "invalid_input"
