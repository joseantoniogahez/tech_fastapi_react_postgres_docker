from typing import Any, Mapping

from .domain import DomainErrorType, DomainException, ErrorLayer


class RouterException(DomainException):
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
            layer=ErrorLayer.ROUTER,
        )


__all__ = ["RouterException"]
