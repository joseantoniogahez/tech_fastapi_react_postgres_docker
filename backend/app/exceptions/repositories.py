from collections.abc import Mapping
from typing import Any

from .domain import DomainError, DomainErrorType, ErrorLayer


class RepositoryError(DomainError):
    def __init__(
        self,
        message: str = "Repository error",
        *,
        error_type: DomainErrorType = DomainErrorType.INTERNAL_ERROR,
        details: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ):
        super().__init__(
            error_type=error_type,
            message=message,
            details=details,
            headers=headers,
            layer=ErrorLayer.REPOSITORY,
        )


class RepositoryConflictError(RepositoryError):
    def __init__(self, message: str = "Conflict", *, details: Any | None = None):
        super().__init__(
            message=message,
            error_type=DomainErrorType.CONFLICT,
            details=details,
        )


class RepositoryInternalError(RepositoryError):
    def __init__(self, message: str = "Internal server error", *, details: Any | None = None):
        super().__init__(
            message=message,
            error_type=DomainErrorType.INTERNAL_ERROR,
            details=details,
        )
