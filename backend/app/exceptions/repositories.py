from typing import Any, Mapping

from .domain import DomainErrorType, DomainException, ErrorLayer


class RepositoryException(DomainException):
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


__all__ = ["RepositoryException"]
