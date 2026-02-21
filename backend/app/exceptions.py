from enum import Enum
from typing import Any, Mapping

from app import ExceptionBase


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
    ):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.details = details
        self.headers = dict(headers) if headers is not None else None


class InvalidInputException(DomainException):
    def __init__(self, message: str = "Invalid input", *, details: Any | None = None):
        super().__init__(DomainErrorType.INVALID_INPUT, message, details=details)


class UnauthorizedException(DomainException):
    def __init__(
        self,
        message: str = "Unauthorized",
        *,
        details: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ):
        auth_headers = {"WWW-Authenticate": "Bearer"}
        if headers is not None:
            auth_headers.update(headers)
        super().__init__(DomainErrorType.UNAUTHORIZED, message, details=details, headers=auth_headers)


class ForbiddenException(DomainException):
    def __init__(self, message: str = "Forbidden", *, details: Any | None = None):
        super().__init__(DomainErrorType.FORBIDDEN, message, details=details)


class NotFoundException(DomainException):
    def __init__(self, message: str = "Not found", *, details: Any | None = None):
        super().__init__(DomainErrorType.NOT_FOUND, message, details=details)


class ConflictException(DomainException):
    def __init__(self, message: str = "Conflict", *, details: Any | None = None):
        super().__init__(DomainErrorType.CONFLICT, message, details=details)
