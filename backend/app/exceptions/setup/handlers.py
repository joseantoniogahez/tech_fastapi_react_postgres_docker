import logging
from typing import Any, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.domain import DomainErrorType, DomainException
from app.exceptions.services import InternalErrorException, InvalidInputException

ERROR_HTTP_STATUS_MAP: dict[DomainErrorType, int] = {
    DomainErrorType.INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
    DomainErrorType.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    DomainErrorType.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    DomainErrorType.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    DomainErrorType.CONFLICT: status.HTTP_409_CONFLICT,
    DomainErrorType.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}
logger = logging.getLogger(__name__)


def build_error_payload(
    *,
    detail: str,
    status_code: int,
    code: str,
    meta: Any | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "detail": detail,
        "status": status_code,
        "code": code,
    }
    if meta is not None:
        payload["meta"] = meta
    return payload


def map_status_to_error_type(status_code: int) -> DomainErrorType:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return DomainErrorType.UNAUTHORIZED
    if status_code == status.HTTP_403_FORBIDDEN:
        return DomainErrorType.FORBIDDEN
    if status_code == status.HTTP_404_NOT_FOUND:
        return DomainErrorType.NOT_FOUND
    if status_code == status.HTTP_409_CONFLICT:
        return DomainErrorType.CONFLICT
    if status_code in {status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY}:
        return DomainErrorType.INVALID_INPUT
    return DomainErrorType.INTERNAL_ERROR


async def domain_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    domain_exc = cast(DomainException, exc)
    status_code = ERROR_HTTP_STATUS_MAP.get(domain_exc.error_type, status.HTTP_500_INTERNAL_SERVER_ERROR)
    payload = build_error_payload(
        detail=domain_exc.detail,
        status_code=status_code,
        code=domain_exc.code,
        meta=domain_exc.meta,
    )
    return JSONResponse(status_code=status_code, content=payload, headers=domain_exc.headers)


async def request_validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_exc = cast(RequestValidationError, exc)
    domain_exc = InvalidInputException(message="Request validation error", details=validation_exc.errors())
    return await domain_exception_handler(request, domain_exc)


async def http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    http_exc = cast(StarletteHTTPException, exc)
    error_type = map_status_to_error_type(http_exc.status_code)
    meta: Any | None = None
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
    )
    return JSONResponse(status_code=http_exc.status_code, content=payload, headers=http_exc.headers)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception captured by global handler", exc_info=exc)
    return await domain_exception_handler(request, InternalErrorException())


def configure_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


__all__ = [
    "ERROR_HTTP_STATUS_MAP",
    "build_error_payload",
    "map_status_to_error_type",
    "domain_exception_handler",
    "request_validation_exception_handler",
    "http_exception_handler",
    "unhandled_exception_handler",
    "configure_exception_handlers",
]
