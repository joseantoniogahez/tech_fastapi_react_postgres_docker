from dataclasses import dataclass
from typing import Annotated, Awaitable, Callable

from fastapi import Depends

from app.const.permission import PermissionScope, normalize_permission_scope
from app.exceptions.services import ForbiddenException
from app.models.user import User

from .authentication import CurrentActiveUserDependency
from .services import AuthServiceDependency

PermissionPolicyDependency = Callable[..., Awaitable[None]]
AuthorizedUserPolicyDependency = Callable[..., Awaitable[User]]
PermissionContextProvider = Callable[..., Awaitable["PermissionResourceContext"]]


@dataclass(frozen=True)
class PermissionResourceContext:
    owner_user_id: int | None = None
    tenant_id: int | None = None


async def allow_public_read_access() -> None:
    return None


PublicReadAccessDependency = Annotated[None, Depends(allow_public_read_access)]


async def allow_authenticated_read_access(current_user: CurrentActiveUserDependency) -> User:
    return current_user


AuthenticatedReadAccessDependency = Annotated[User, Depends(allow_authenticated_read_access)]


async def build_default_permission_context() -> PermissionResourceContext:
    return PermissionResourceContext()


async def build_current_user_permission_context(current_user: CurrentActiveUserDependency) -> PermissionResourceContext:
    return PermissionResourceContext(
        owner_user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )


async def build_current_tenant_permission_context(
    current_user: CurrentActiveUserDependency,
) -> PermissionResourceContext:
    return PermissionResourceContext(tenant_id=current_user.tenant_id)


def require_permission(
    permission_id: str,
    *,
    required_scope: str = PermissionScope.ANY,
    resource_context_dependency: PermissionContextProvider = build_default_permission_context,
) -> PermissionPolicyDependency:
    normalized_required_scope = normalize_permission_scope(required_scope)

    async def dependency(
        current_user: CurrentActiveUserDependency,
        auth_service: AuthServiceDependency,
        resource_context: Annotated[PermissionResourceContext, Depends(resource_context_dependency)],
    ) -> None:
        has_permission = await auth_service.user_has_permission(
            user_id=current_user.id,
            permission_id=permission_id,
            required_scope=normalized_required_scope,
            resource_owner_id=resource_context.owner_user_id,
            resource_tenant_id=resource_context.tenant_id,
            user_tenant_id=current_user.tenant_id,
        )
        if not has_permission:
            raise ForbiddenException(
                message=f"Missing required permission: {permission_id}",
                details={"permission_id": permission_id},
            )

    return dependency


def require_authorized_user(
    permission_id: str,
    *,
    required_scope: str = PermissionScope.ANY,
    resource_context_dependency: PermissionContextProvider = build_default_permission_context,
) -> AuthorizedUserPolicyDependency:
    async def dependency(
        current_user: CurrentActiveUserDependency,
        _: Annotated[
            None,
            Depends(
                require_permission(
                    permission_id,
                    required_scope=required_scope,
                    resource_context_dependency=resource_context_dependency,
                )
            ),
        ],
    ) -> User:
        return current_user

    return dependency
