import logging
from typing import Any, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.domain import DomainError, DomainErrorType
from app.exceptions.services import InternalError, InvalidInputError

ERROR_HTTP_STATUS_MAP: dict[DomainErrorType, int] = {
    DomainErrorType.INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
    DomainErrorType.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    DomainErrorType.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    DomainErrorType.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    DomainErrorType.CONFLICT: status.HTTP_409_CONFLICT,
    DomainErrorType.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}
REQUEST_ID_HEADER = "X-Request-ID"
logger = logging.getLogger(__name__)


def build_error_payload(
    *,
    detail: str,
    status_code: int,
    code: str,
    meta: Any | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "detail": detail,
        "status": status_code,
        "code": code,
    }
    if meta is not None:
        payload["meta"] = meta
    if request_id is not None:
        payload["request_id"] = request_id
    return payload


def get_request_id(request: Request) -> str | None:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    return None


def build_response_headers(
    headers: dict[str, str] | None,
    request_id: str | None,
) -> dict[str, str] | None:
    response_headers = dict(headers or {})
    if request_id is not None:
        response_headers.setdefault(REQUEST_ID_HEADER, request_id)
    return response_headers or None


def map_status_to_error_type(status_code: int) -> DomainErrorType:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return DomainErrorType.UNAUTHORIZED
    if status_code == status.HTTP_403_FORBIDDEN:
        return DomainErrorType.FORBIDDEN
    if status_code == status.HTTP_404_NOT_FOUND:
        return DomainErrorType.NOT_FOUND
    if status_code == status.HTTP_409_CONFLICT:
        return DomainErrorType.CONFLICT
    if status_code in {status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_CONTENT}:
        return DomainErrorType.INVALID_INPUT
    return DomainErrorType.INTERNAL_ERROR


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    domain_exc = cast(DomainError, exc)
    status_code = ERROR_HTTP_STATUS_MAP.get(domain_exc.error_type, status.HTTP_500_INTERNAL_SERVER_ERROR)
    request_id = get_request_id(request)
    payload = build_error_payload(
        detail=domain_exc.detail,
        status_code=status_code,
        code=domain_exc.code,
        meta=domain_exc.meta,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers=build_response_headers(domain_exc.headers, request_id),
    )


async def request_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_exc = cast(RequestValidationError, exc)
    domain_exc = InvalidInputError(message="Request validation error", details=validation_exc.errors())
    return await domain_error_handler(request, domain_exc)


async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    http_exc = cast(StarletteHTTPException, exc)
    error_type = map_status_to_error_type(http_exc.status_code)
    meta: Any | None = None
    request_id = get_request_id(request)
    if isinstance(http_exc.detail, str):
        detail = http_exc.detail
    else:
        detail = "HTTP error"
        meta = http_exc.detail
    payload = build_error_payload(
        detail=detail,
        status_code=http_exc.status_code,
        code=error_type.value,
        meta=meta,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=http_exc.status_code,
        content=payload,
        headers=build_response_headers(http_exc.headers, request_id),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)
    logger.exception(
        "event=api_unhandled_error request_id=%s method=%s path=%s",
        request_id or "-",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return await domain_error_handler(request, InternalError())


def configure_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
