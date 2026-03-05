from typing import Annotated, cast

from fastapi import Depends, Request

from app.const.settings import AuthSettings
from app.services.auth import AuthService, AuthServicePort
from app.services.author import AuthorService, AuthorServicePort
from app.services.book import BookService, BookServicePort
from app.services.password_service import Argon2PasswordService, PasswordServicePort
from app.services.rbac import RBACService, RBACServicePort
from app.services.token_service import JwtTokenService, TokenServicePort

from .db import UnitOfWorkDependency
from .repositories import (
    AuthorRepositoryDependency,
    AuthRepositoryDependency,
    BookRepositoryDependency,
    RBACRepositoryDependency,
)

PermissionScopeCache = dict[tuple[int, str], str | None]
_PERMISSION_SCOPE_CACHE_STATE_KEY = "_permission_scope_cache"


async def get_request_permission_scope_cache(request: Request) -> PermissionScopeCache:
    cache = getattr(request.state, _PERMISSION_SCOPE_CACHE_STATE_KEY, None)
    if isinstance(cache, dict):
        return cast(PermissionScopeCache, cache)

    request_scope_cache: PermissionScopeCache = {}
    setattr(request.state, _PERMISSION_SCOPE_CACHE_STATE_KEY, request_scope_cache)
    return request_scope_cache


PermissionScopeCacheDependency = Annotated[PermissionScopeCache, Depends(get_request_permission_scope_cache)]


async def get_author_service(
    author_repository: AuthorRepositoryDependency,
    unit_of_work: UnitOfWorkDependency,
) -> AuthorServicePort:
    return AuthorService(author_repository=author_repository, unit_of_work=unit_of_work)


AuthorServiceDependency = Annotated[AuthorServicePort, Depends(get_author_service)]


async def get_book_service(
    book_repository: BookRepositoryDependency,
    author_service: AuthorServiceDependency,
    unit_of_work: UnitOfWorkDependency,
) -> BookServicePort:
    return BookService(
        book_repository=book_repository,
        author_service=author_service,
        unit_of_work=unit_of_work,
    )


BookServiceDependency = Annotated[BookServicePort, Depends(get_book_service)]


async def get_auth_settings() -> AuthSettings:
    return AuthSettings()


AuthSettingsDependency = Annotated[AuthSettings, Depends(get_auth_settings)]


async def get_password_service() -> PasswordServicePort:
    return Argon2PasswordService()


PasswordServiceDependency = Annotated[PasswordServicePort, Depends(get_password_service)]


async def get_token_service(auth_settings: AuthSettingsDependency) -> TokenServicePort:
    return JwtTokenService(auth_settings)


TokenServiceDependency = Annotated[TokenServicePort, Depends(get_token_service)]


async def get_auth_service(
    auth_repository: AuthRepositoryDependency,
    auth_settings: AuthSettingsDependency,
    token_service: TokenServiceDependency,
    password_service: PasswordServiceDependency,
    unit_of_work: UnitOfWorkDependency,
    permission_scope_cache: PermissionScopeCacheDependency,
) -> AuthServicePort:
    return AuthService(
        auth_repository=auth_repository,
        unit_of_work=unit_of_work,
        auth_settings=auth_settings,
        token_service=token_service,
        password_service=password_service,
        permission_scope_cache=permission_scope_cache,
    )


AuthServiceDependency = Annotated[AuthServicePort, Depends(get_auth_service)]


async def get_rbac_service(
    rbac_repository: RBACRepositoryDependency,
    unit_of_work: UnitOfWorkDependency,
) -> RBACServicePort:
    return RBACService(
        rbac_repository=rbac_repository,
        unit_of_work=unit_of_work,
    )


RBACServiceDependency = Annotated[RBACServicePort, Depends(get_rbac_service)]
