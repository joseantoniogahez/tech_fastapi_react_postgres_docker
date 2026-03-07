import logging
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.observability import log_layer_event

logger = logging.getLogger("app.uow")


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._scope_depth = 0
        self._rollback_only = False

    async def __aenter__(self) -> UnitOfWork:
        self._scope_depth += 1
        log_layer_event(
            logger,
            layer="infrastructure",
            event="uow_scope_enter",
            depth=self._scope_depth,
        )
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
            log_layer_event(
                logger,
                layer="infrastructure",
                event="uow_scope_exit_nested",
                depth=self._scope_depth,
                rollback_only=self._rollback_only,
            )
            return

        if self._rollback_only:
            log_layer_event(
                logger,
                layer="infrastructure",
                event="uow_scope_exit_rollback_only",
            )
            self._rollback_only = False
            return

        await self.commit()

    async def commit(self) -> None:
        await self.session.commit()
        self._rollback_only = False
        log_layer_event(
            logger,
            layer="infrastructure",
            event="uow_commit",
        )

    async def rollback(self) -> None:
        await self.session.rollback()
        self._rollback_only = True
        log_layer_event(
            logger,
            layer="infrastructure",
            event="uow_rollback",
        )
