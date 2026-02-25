from typing import Annotated

from fastapi import Depends

from app.const.settings import AuthSettings
from app.services.auth import AuthService, AuthServicePort
from app.services.author import AuthorService, AuthorServicePort
from app.services.book import BookService, BookServicePort

from .db import UnitOfWorkDependency
from .repositories import AuthorRepositoryDependency, AuthRepositoryDependency, BookRepositoryDependency


async def get_authors_service(
    author_repository: AuthorRepositoryDependency,
    unit_of_work: UnitOfWorkDependency,
) -> AuthorServicePort:
    return AuthorService(author_repository=author_repository, unit_of_work=unit_of_work)


AuthorServiceDependency = Annotated[AuthorServicePort, Depends(get_authors_service)]


async def get_books_service(
    book_repository: BookRepositoryDependency,
    author_service: AuthorServiceDependency,
    unit_of_work: UnitOfWorkDependency,
) -> BookServicePort:
    return BookService(
        book_repository=book_repository,
        author_service=author_service,
        unit_of_work=unit_of_work,
    )


BookServiceDependency = Annotated[BookServicePort, Depends(get_books_service)]


async def get_auth_settings() -> AuthSettings:
    return AuthSettings()


AuthSettingsDependency = Annotated[AuthSettings, Depends(get_auth_settings)]


async def get_auth_service(
    auth_repository: AuthRepositoryDependency,
    auth_settings: AuthSettingsDependency,
    unit_of_work: UnitOfWorkDependency,
) -> AuthServicePort:
    return AuthService(
        auth_repository=auth_repository,
        unit_of_work=unit_of_work,
        auth_settings=auth_settings,
    )


AuthServiceDependency = Annotated[AuthServicePort, Depends(get_auth_service)]


__all__ = [
    "BookServiceDependency",
    "AuthorServiceDependency",
    "AuthServiceDependency",
    "AuthSettingsDependency",
    "get_books_service",
    "get_authors_service",
    "get_auth_service",
    "get_auth_settings",
]
