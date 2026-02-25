from types import TracebackType
from typing import Protocol


class UnitOfWorkPort(Protocol):
    async def __aenter__(self) -> "UnitOfWorkPort": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class Service:
    pass
