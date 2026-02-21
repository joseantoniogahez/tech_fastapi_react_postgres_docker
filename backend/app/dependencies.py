from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.const.settings import AuthSettings
from app.database import AsyncSessionDatabase
from app.models.user import User
from app.repositories.author import AuthorRepository
from app.repositories.book import BookRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.author import AuthorService
from app.services.book import BookService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

INVALID_TOKEN_EXCEPTION = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
INACTIVE_USER_EXCEPTION = HTTPException(
    status_code=403,
    detail="Inactive user",
)


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


async def get_user_repository(session: DbSessionDependency) -> UserRepository:
    return UserRepository(session=session)


UserRepositoryDependency = Annotated[UserRepository, Depends(get_user_repository)]


async def get_books_service(
    book_repository: BookRepositoryDependency,
    author_repository: AuthorRepositoryDependency,
) -> BookService:
    return BookService(book_repository=book_repository, author_repository=author_repository)


BookServiceDependency = Annotated[BookService, Depends(get_books_service)]


async def get_authors_service(author_repository: AuthorRepositoryDependency) -> AuthorService:
    return AuthorService(author_repository=author_repository)


AuthorServiceDependency = Annotated[AuthorService, Depends(get_authors_service)]


async def get_auth_service(user_repository: UserRepositoryDependency) -> AuthService:
    return AuthService(user_repository=user_repository, auth_settings=AuthSettings())


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthServiceDependency,
) -> User:
    user = await auth_service.get_user_from_token(token)
    if user is None:
        raise INVALID_TOKEN_EXCEPTION
    return user


CurrentUserDependency = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUserDependency) -> User:
    if current_user.disabled:
        raise INACTIVE_USER_EXCEPTION
    return current_user


CurrentActiveUserDependency = Annotated[User, Depends(get_current_active_user)]
