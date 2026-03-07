import asyncio
import json
from typing import Any, cast
from unittest.mock import patch

import pytest
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.core.errors.domain import DomainError, DomainErrorType, ErrorLayer
from app.core.errors.repositories import RepositoryConflictError, RepositoryError, RepositoryInternalError
from app.core.errors.routers import RouterError
from app.core.errors.services import UnauthorizedError
from app.core.errors.setup.handlers import (
    REQUEST_ID_HEADER,
    build_error_payload,
    configure_exception_handlers,
    domain_error_handler,
    get_request_id,
    http_error_handler,
    map_status_to_error_type,
    request_validation_error_handler,
    unhandled_error_handler,
)


def _request(request_id: str | None = None) -> Request:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "http_version": "1.1",
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
    )
    if request_id is not None:
        request.state.request_id = request_id
    return request


def _payload(response: JSONResponse) -> dict[str, Any]:
    response_body = cast(bytes, response.body)
    return json.loads(response_body.decode("utf-8"))


def test_repository_and_router_exception_set_expected_layer() -> None:
    repository_exc = RepositoryError(message="Repo failure")
    repository_conflict_exc = RepositoryConflictError(message="Repo conflict")
    repository_internal_exc = RepositoryInternalError()
    router_exc = RouterError(DomainErrorType.NOT_FOUND, "Route failure")

    assert repository_exc.layer == ErrorLayer.REPOSITORY
    assert repository_exc.code == DomainErrorType.INTERNAL_ERROR.value
    assert repository_conflict_exc.layer == ErrorLayer.REPOSITORY
    assert repository_conflict_exc.code == DomainErrorType.CONFLICT.value
    assert repository_internal_exc.layer == ErrorLayer.REPOSITORY
    assert repository_internal_exc.code == DomainErrorType.INTERNAL_ERROR.value
    assert router_exc.layer == ErrorLayer.ROUTER
    assert router_exc.code == DomainErrorType.NOT_FOUND.value


def test_unauthorized_exception_merges_headers() -> None:
    exc = UnauthorizedError(headers={"X-Reason": "expired"})
    assert exc.headers == {
        "WWW-Authenticate": "Bearer",
        "X-Reason": "expired",
    }


def test_build_error_payload_handles_optional_meta() -> None:
    no_meta = build_error_payload(detail="Invalid", status_code=400, code="invalid_input")
    with_meta = build_error_payload(
        detail="Invalid",
        status_code=400,
        code="invalid_input",
        meta={"field": "title"},
        request_id="req-123",
    )

    assert no_meta == {"detail": "Invalid", "status": 400, "code": "invalid_input"}
    assert with_meta == {
        "detail": "Invalid",
        "status": 400,
        "code": "invalid_input",
        "meta": {"field": "title"},
        "request_id": "req-123",
    }


def test_get_request_id_returns_none_when_request_has_no_context() -> None:
    assert get_request_id(_request()) is None


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (status.HTTP_401_UNAUTHORIZED, DomainErrorType.UNAUTHORIZED),
        (status.HTTP_403_FORBIDDEN, DomainErrorType.FORBIDDEN),
        (status.HTTP_404_NOT_FOUND, DomainErrorType.NOT_FOUND),
        (status.HTTP_409_CONFLICT, DomainErrorType.CONFLICT),
        (status.HTTP_400_BAD_REQUEST, DomainErrorType.INVALID_INPUT),
        (status.HTTP_500_INTERNAL_SERVER_ERROR, DomainErrorType.INTERNAL_ERROR),
    ],
)
def test_map_status_to_error_type(status_code: int, expected: DomainErrorType) -> None:
    assert map_status_to_error_type(status_code) == expected


def test_request_validation_exception_handler_returns_invalid_input() -> None:
    validation_exc = RequestValidationError(
        [
            {
                "type": "missing",
                "loc": ("body", "title"),
                "msg": "Field required",
                "input": {},
            }
        ]
    )

    response = asyncio.run(request_validation_error_handler(_request("req-123"), validation_exc))
    payload = _payload(response)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert payload["detail"] == "Request validation error"
    assert payload["code"] == DomainErrorType.INVALID_INPUT.value
    assert payload["request_id"] == "req-123"
    assert payload["meta"][0]["loc"] == ["body", "title"]
    assert response.headers[REQUEST_ID_HEADER] == "req-123"


def test_http_exception_handler_with_string_detail() -> None:
    exc = StarletteHTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Denied", headers={"X-Rule": "rbac"})

    response = asyncio.run(http_error_handler(_request("req-123"), exc))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.headers["x-rule"] == "rbac"
    assert response.headers[REQUEST_ID_HEADER] == "req-123"
    assert _payload(response) == {
        "detail": "Denied",
        "status": status.HTTP_403_FORBIDDEN,
        "code": DomainErrorType.FORBIDDEN.value,
        "request_id": "req-123",
    }


def test_http_exception_handler_with_non_string_detail() -> None:
    exc = StarletteHTTPException(
        status_code=status.HTTP_418_IM_A_TEAPOT,
        detail=cast(Any, {"reason": "teapot"}),
    )

    response = asyncio.run(http_error_handler(_request("req-123"), exc))

    assert response.status_code == status.HTTP_418_IM_A_TEAPOT
    assert response.headers[REQUEST_ID_HEADER] == "req-123"
    assert _payload(response) == {
        "detail": "HTTP error",
        "status": status.HTTP_418_IM_A_TEAPOT,
        "code": DomainErrorType.INTERNAL_ERROR.value,
        "meta": {"reason": "teapot"},
        "request_id": "req-123",
    }


def test_unhandled_exception_handler_logs_and_returns_internal_error() -> None:
    with patch("app.core.errors.setup.handlers.logger.exception") as logger_exception:
        response = asyncio.run(unhandled_error_handler(_request("req-123"), RuntimeError("boom")))

    logger_exception.assert_called_once()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.headers[REQUEST_ID_HEADER] == "req-123"
    assert _payload(response) == {
        "detail": "Internal server error",
        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "code": DomainErrorType.INTERNAL_ERROR.value,
        "request_id": "req-123",
    }


def test_configure_exception_handlers_registers_all_handlers() -> None:
    app = FastAPI()
    configure_exception_handlers(app)

    assert app.exception_handlers[DomainError] is domain_error_handler
    assert app.exception_handlers[RequestValidationError] is request_validation_error_handler
    assert app.exception_handlers[StarletteHTTPException] is http_error_handler
    assert app.exception_handlers[Exception] is unhandled_error_handler
