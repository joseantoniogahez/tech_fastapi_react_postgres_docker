from typing import Annotated, Awaitable, Callable

from fastapi import Depends

from app.const.permission import PermissionId
from app.exceptions import ForbiddenException
from app.models.user import User

from .providers import AuthServiceDependency, CurrentActiveUserDependency

PermissionPolicyDependency = Callable[..., Awaitable[None]]
AuthorizedUserPolicyDependency = Callable[..., Awaitable[User]]


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


BookCreateAuthorizedUserDependency = Annotated[User, Depends(require_authorized_user(PermissionId.BOOK_CREATE))]
BookUpdateAuthorizedUserDependency = Annotated[User, Depends(require_authorized_user(PermissionId.BOOK_UPDATE))]
BookDeleteAuthorizedUserDependency = Annotated[User, Depends(require_authorized_user(PermissionId.BOOK_DELETE))]


__all__ = [
    "PermissionPolicyDependency",
    "AuthorizedUserPolicyDependency",
    "require_permission",
    "require_authorized_user",
    "BookCreateAuthorizedUserDependency",
    "BookUpdateAuthorizedUserDependency",
    "BookDeleteAuthorizedUserDependency",
]
