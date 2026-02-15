from http import HTTPStatus

from starlette.testclient import TestClient


def test_health_returns_ok(mock_client: TestClient) -> None:
    response = mock_client.get("/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}
