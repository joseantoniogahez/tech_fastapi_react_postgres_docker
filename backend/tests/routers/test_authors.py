from http import HTTPStatus

from starlette.testclient import TestClient


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
