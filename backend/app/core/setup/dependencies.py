from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import AuthSettings
from app.core.db.database import get_async_session_factory
from app.core.db.ports import UnitOfWorkPort
from app.core.db.uow import UnitOfWork
from app.core.security.service import Argon2PasswordService, JwtTokenService, PasswordServicePort, TokenServicePort
from app.features.auth.repository import AuthRepository
from app.features.auth.service import AuthService, AuthServicePort
from app.features.outbox.repository import OutboxRepository
from app.features.outbox.service import OutboxService, OutboxServicePort
from app.features.rbac.repository import RBACRepository
from app.features.rbac.service import RBACService, RBACServicePort

PermissionScopeCache = dict[tuple[int, str], str | None]
_PERMISSION_SCOPE_CACHE_STATE_KEY = "_permission_scope_cache"


def create_async_session() -> AsyncSession:
    return get_async_session_factory()()


async def get_db_session():
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


async def get_request_permission_scope_cache(request: Request) -> PermissionScopeCache:
    cache = getattr(request.state, _PERMISSION_SCOPE_CACHE_STATE_KEY, None)
    if isinstance(cache, dict):
        return cast(PermissionScopeCache, cache)

    request_scope_cache: PermissionScopeCache = {}
    setattr(request.state, _PERMISSION_SCOPE_CACHE_STATE_KEY, request_scope_cache)
    return request_scope_cache


PermissionScopeCacheDependency = Annotated[PermissionScopeCache, Depends(get_request_permission_scope_cache)]


async def get_auth_repository(session: DbSessionDependency):
    return AuthRepository(session=session)


AuthRepositoryDependency = Annotated[AuthRepository, Depends(get_auth_repository)]


async def get_rbac_repository(session: DbSessionDependency):
    return RBACRepository(session=session)


RBACRepositoryDependency = Annotated[RBACRepository, Depends(get_rbac_repository)]


async def get_outbox_repository(session: DbSessionDependency):
    return OutboxRepository(session=session)


OutboxRepositoryDependency = Annotated[OutboxRepository, Depends(get_outbox_repository)]


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


async def get_outbox_service(
    outbox_repository: OutboxRepositoryDependency,
    unit_of_work: UnitOfWorkDependency,
) -> OutboxServicePort:
    return OutboxService(
        outbox_repository=outbox_repository,
        unit_of_work=unit_of_work,
    )


OutboxServiceDependency = Annotated[OutboxServicePort, Depends(get_outbox_service)]
