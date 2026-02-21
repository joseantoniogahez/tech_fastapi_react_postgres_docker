from enum import Enum
from typing import Any, Mapping

from app import ExceptionBase


class ErrorLayer(str, Enum):
    DOMAIN = "domain"
    ROUTER = "router"
    SERVICE = "service"
    REPOSITORY = "repository"


class DomainErrorType(str, Enum):
    INVALID_INPUT = "invalid_input"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    INTERNAL_ERROR = "internal_error"


class DomainException(ExceptionBase):
    def __init__(
        self,
        error_type: DomainErrorType,
        message: str,
        *,
        details: Any | None = None,
        headers: Mapping[str, str] | None = None,
        layer: ErrorLayer = ErrorLayer.DOMAIN,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.detail = message
        self.details = details
        self.meta = details
        self.code = error_type.value
        self.layer = layer
        self.headers = dict(headers) if headers is not None else None


__all__ = [
    "ErrorLayer",
    "DomainErrorType",
    "DomainException",
]
