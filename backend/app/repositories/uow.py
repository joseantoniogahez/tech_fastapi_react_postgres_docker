from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._scope_depth = 0
        self._rollback_only = False

    async def __aenter__(self) -> UnitOfWork:
        self._scope_depth += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None and not self._rollback_only:
            await self.rollback()

        self._scope_depth -= 1
        if self._scope_depth > 0:
            return

        if self._rollback_only:
            self._rollback_only = False
            return

        await self.commit()

    async def commit(self) -> None:
        await self.session.commit()
        self._rollback_only = False

    async def rollback(self) -> None:
        await self.session.rollback()
        self._rollback_only = True
