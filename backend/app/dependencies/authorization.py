from typing import Annotated, Awaitable, Callable

from fastapi import Depends

from app.exceptions.services import ForbiddenException
from app.models.user import User

from .authentication import CurrentActiveUserDependency
from .services import AuthServiceDependency

PermissionPolicyDependency = Callable[..., Awaitable[None]]
AuthorizedUserPolicyDependency = Callable[..., Awaitable[User]]


async def allow_public_read_access() -> None:
    return None


PublicReadAccessDependency = Annotated[None, Depends(allow_public_read_access)]


async def allow_authenticated_read_access(current_user: CurrentActiveUserDependency) -> User:
    return current_user


AuthenticatedReadAccessDependency = Annotated[User, Depends(allow_authenticated_read_access)]


def require_permission(permission_id: str) -> PermissionPolicyDependency:
    async def dependency(
        current_user: CurrentActiveUserDependency,
        auth_service: AuthServiceDependency,
    ) -> None:
        has_permission = await auth_service.user_has_permission(user_id=current_user.id, permission_id=permission_id)
        if not has_permission:
            raise ForbiddenException(
                message=f"Missing required permission: {permission_id}",
                details={"permission_id": permission_id},
            )

    return dependency


def require_authorized_user(permission_id: str) -> AuthorizedUserPolicyDependency:
    async def dependency(
        current_user: CurrentActiveUserDependency,
        _: Annotated[None, Depends(require_permission(permission_id))],
    ) -> User:
        return current_user

    return dependency
