from typing import Any, Mapping

from .domain import DomainErrorType, DomainException, ErrorLayer


class ServiceException(DomainException):
    def __init__(
        self,
        error_type: DomainErrorType,
        message: str,
        *,
        details: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ):
        super().__init__(
            error_type=error_type,
            message=message,
            details=details,
            headers=headers,
            layer=ErrorLayer.SERVICE,
        )


class InvalidInputException(ServiceException):
    def __init__(self, message: str = "Invalid input", *, details: Any | None = None):
        super().__init__(DomainErrorType.INVALID_INPUT, message, details=details)


class UnauthorizedException(ServiceException):
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


class ForbiddenException(ServiceException):
    def __init__(self, message: str = "Forbidden", *, details: Any | None = None):
        super().__init__(DomainErrorType.FORBIDDEN, message, details=details)


class NotFoundException(ServiceException):
    def __init__(self, message: str = "Not found", *, details: Any | None = None):
        super().__init__(DomainErrorType.NOT_FOUND, message, details=details)


class ConflictException(ServiceException):
    def __init__(self, message: str = "Conflict", *, details: Any | None = None):
        super().__init__(DomainErrorType.CONFLICT, message, details=details)


class InternalErrorException(ServiceException):
    def __init__(self, message: str = "Internal server error", *, details: Any | None = None):
        super().__init__(DomainErrorType.INTERNAL_ERROR, message, details=details)


__all__ = [
    "ServiceException",
    "InvalidInputException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "ConflictException",
    "InternalErrorException",
]
