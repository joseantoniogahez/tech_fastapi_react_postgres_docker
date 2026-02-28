from typing import Annotated

from fastapi import Depends

from app.repositories.auth import AuthRepository
from app.repositories.author import AuthorRepository
from app.repositories.book import BookRepository
from app.repositories.rbac import RBACRepository
from app.services.auth import AuthRepositoryPort
from app.services.author import AuthorRepositoryPort
from app.services.book import BookRepositoryPort
from app.services.rbac import RBACRepositoryPort

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


async def get_rbac_repository(session: DbSessionDependency) -> RBACRepositoryPort:
    return RBACRepository(session=session)


RBACRepositoryDependency = Annotated[RBACRepositoryPort, Depends(get_rbac_repository)]
