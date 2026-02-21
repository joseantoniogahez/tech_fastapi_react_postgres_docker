from typing import Annotated, AsyncGenerator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.const.settings import AuthSettings
from app.database import AsyncSessionDatabase
from app.exceptions import ForbiddenException
from app.models.user import User
from app.repositories.auth import AuthRepository
from app.repositories.author import AuthorRepository
from app.repositories.book import BookRepository
from app.schemas.auth import Credentials
from app.services.auth import AuthService
from app.services.author import AuthorService
from app.services.book import BookService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
BearerTokenDependency = Annotated[str, Depends(oauth2_scheme)]


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


async def get_auth_repository(session: DbSessionDependency) -> AuthRepository:
    return AuthRepository(session=session)


AuthRepositoryDependency = Annotated[AuthRepository, Depends(get_auth_repository)]


async def get_books_service(
    book_repository: BookRepositoryDependency,
    author_repository: AuthorRepositoryDependency,
) -> BookService:
    return BookService(book_repository=book_repository, author_repository=author_repository)


BookServiceDependency = Annotated[BookService, Depends(get_books_service)]


async def get_authors_service(author_repository: AuthorRepositoryDependency) -> AuthorService:
    return AuthorService(author_repository=author_repository)


AuthorServiceDependency = Annotated[AuthorService, Depends(get_authors_service)]


async def get_auth_settings() -> AuthSettings:
    return AuthSettings()


AuthSettingsDependency = Annotated[AuthSettings, Depends(get_auth_settings)]


async def get_auth_credentials(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Credentials:
    return Credentials(username=form_data.username, password=form_data.password)


AuthCredentialsDependency = Annotated[Credentials, Depends(get_auth_credentials)]


async def get_auth_service(
    auth_repository: AuthRepositoryDependency,
    auth_settings: AuthSettingsDependency,
) -> AuthService:
    return AuthService(auth_repository=auth_repository, auth_settings=auth_settings)


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    token: BearerTokenDependency,
    auth_service: AuthServiceDependency,
) -> User:
    return await auth_service.get_user_from_token(token)


CurrentUserDependency = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUserDependency) -> User:
    if current_user.disabled:
        raise ForbiddenException(message="Inactive user")
    return current_user


CurrentActiveUserDependency = Annotated[User, Depends(get_current_active_user)]


__all__ = [
    "BearerTokenDependency",
    "DbSessionDependency",
    "BookRepositoryDependency",
    "AuthorRepositoryDependency",
    "AuthRepositoryDependency",
    "BookServiceDependency",
    "AuthorServiceDependency",
    "AuthServiceDependency",
    "AuthCredentialsDependency",
    "CurrentUserDependency",
    "CurrentActiveUserDependency",
    "get_db_session",
    "get_book_repository",
    "get_author_repository",
    "get_auth_repository",
    "get_books_service",
    "get_authors_service",
    "get_auth_service",
    "get_auth_settings",
    "get_auth_credentials",
    "get_current_user",
    "get_current_active_user",
]
