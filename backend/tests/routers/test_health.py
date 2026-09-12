from http import HTTPStatus
from typing import cast
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.core.setup.dependencies import get_readiness_service
from app.features.health.schemas import ReadinessCheckResponse, ReadinessResponse, ReadinessStatus
from app.features.health.service import ReadinessService


def test_health_returns_ok(mock_client: TestClient) -> None:
    cast(FastAPI, mock_client.app).dependency_overrides[get_readiness_service] = lambda: (_ for _ in ()).throw(
        AssertionError("liveness must not resolve readiness dependencies")
    )

    response = mock_client.get("/v1/health")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


def test_readiness_returns_typed_ok_response(mock_client: TestClient) -> None:
    service = MagicMock(spec=ReadinessService)
    service.evaluate = AsyncMock(
        return_value=ReadinessResponse(
            status=ReadinessStatus.OK,
            checks=[ReadinessCheckResponse(name="database", status=ReadinessStatus.OK)],
        )
    )
    cast(FastAPI, mock_client.app).dependency_overrides[get_readiness_service] = lambda: service

    response = mock_client.get("/v1/readiness")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "status": "ok",
        "checks": [{"name": "database", "status": "ok"}],
    }


def test_readiness_returns_typed_safe_503_response(mock_client: TestClient) -> None:
    service = MagicMock(spec=ReadinessService)
    service.evaluate = AsyncMock(
        return_value=ReadinessResponse(
            status=ReadinessStatus.UNAVAILABLE,
            checks=[ReadinessCheckResponse(name="database", status=ReadinessStatus.UNAVAILABLE)],
        )
    )
    cast(FastAPI, mock_client.app).dependency_overrides[get_readiness_service] = lambda: service

    response = mock_client.get("/v1/readiness")

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {
        "status": "unavailable",
        "checks": [{"name": "database", "status": "unavailable"}],
    }
