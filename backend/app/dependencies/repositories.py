from typing import Annotated

from fastapi import Depends

from app.repositories.auth import AuthRepository
from app.repositories.author import AuthorRepository
from app.repositories.book import BookRepository
from app.services.auth import AuthRepositoryPort
from app.services.author import AuthorRepositoryPort
from app.services.book import BookRepositoryPort

from .db import DbSessionDependency


async def get_book_repository(session: DbSessionDependency) -> BookRepositoryPort:
    return BookRepository(session=session)


BookRepositoryDependency = Annotated[BookRepositoryPort, Depends(get_book_repository)]


async def get_author_repository(session: DbSessionDependency) -> AuthorRepositoryPort:
    return AuthorRepository(session=session)


AuthorRepositoryDependency = Annotated[AuthorRepositoryPort, Depends(get_author_repository)]


async def get_auth_repository(session: DbSessionDependency) -> AuthRepositoryPort:
    return AuthRepository(session=session)


AuthRepositoryDependency = Annotated[AuthRepositoryPort, Depends(get_auth_repository)]


__all__ = [
    "BookRepositoryDependency",
    "AuthorRepositoryDependency",
    "AuthRepositoryDependency",
    "get_book_repository",
    "get_author_repository",
    "get_auth_repository",
]
