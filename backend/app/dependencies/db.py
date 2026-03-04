from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_async_session_factory
from app.repositories.uow import UnitOfWork
from app.services import UnitOfWorkPort


def create_async_session() -> AsyncSession:
    return get_async_session_factory()()


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with create_async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DbSessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


async def get_unit_of_work(session: DbSessionDependency) -> UnitOfWorkPort:
    return UnitOfWork(session=session)


UnitOfWorkDependency = Annotated[UnitOfWorkPort, Depends(get_unit_of_work)]
