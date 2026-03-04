from collections.abc import Mapping
from typing import Any

from .domain import DomainError, DomainErrorType, ErrorLayer


class RouterError(DomainError):
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
