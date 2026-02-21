from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionDatabase
from app.repositories.author import AuthorRepository
from app.repositories.book import BookRepository
from app.services.author import AuthorService
from app.services.book import BookService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionDatabase() as session:
        yield session


DbSessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


async def get_book_repository(session: DbSessionDependency) -> BookRepository:
    return BookRepository(session=session)


BookRepositoryDependency = Annotated[BookRepository, Depends(get_book_repository)]


async def get_author_repository(session: DbSessionDependency) -> AuthorRepository:
    return AuthorRepository(session=session)


AuthorRepositoryDependency = Annotated[AuthorRepository, Depends(get_author_repository)]


async def get_books_service(
    book_repository: BookRepositoryDependency,
    author_repository: AuthorRepositoryDependency,
) -> BookService:
    return BookService(book_repository=book_repository, author_repository=author_repository)


BookServiceDependency = Annotated[BookService, Depends(get_books_service)]


async def get_authors_service(author_repository: AuthorRepositoryDependency) -> AuthorService:
    return AuthorService(author_repository=author_repository)


AuthorServiceDependency = Annotated[AuthorService, Depends(get_authors_service)]
