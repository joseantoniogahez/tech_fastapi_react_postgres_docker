from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionDatabase
from app.services.book import BookService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionDatabase() as session:
        yield session


DbSessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


async def get_books_service(session: DbSessionDependency) -> BookService:
    return BookService(session=session)


BookServiceDependency = Annotated[BookService, Depends(get_books_service)]
