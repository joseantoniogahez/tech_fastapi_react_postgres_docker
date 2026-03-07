import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from app.core.authorization import PermissionScope, normalize_permission_scope
from app.core.errors.services import ForbiddenError
from app.core.setup.dependencies import AuthServiceDependency
from app.features.auth.dependencies import CurrentActiveUserDependency
from app.features.auth.principal import CurrentPrincipal

logger = logging.getLogger("app.authz")

PermissionPolicyDependency = Callable[..., Awaitable[None]]
AuthorizedUserPolicyDependency = Callable[..., Awaitable[CurrentPrincipal]]
PermissionContextProvider = Callable[..., Awaitable["PermissionResourceContext"]]
ConditionalPermissionPolicyDependency = Callable[..., Awaitable[bool]]


@dataclass(frozen=True)
class PermissionResourceContext:
    owner_user_id: int | None = None
    tenant_id: int | None = None


async def allow_public_read_access() -> None:
    return None


PublicReadAccessDependency = Annotated[None, Depends(allow_public_read_access)]


async def allow_authenticated_read_access(current_user: CurrentActiveUserDependency) -> CurrentPrincipal:
    return current_user


AuthenticatedReadAccessDependency = Annotated[CurrentPrincipal, Depends(allow_authenticated_read_access)]


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


async def allow_conditional_permission_policy() -> bool:
    return True


def _get_route_template(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str) and route_path:
        return route_path
    return request.url.path


def _get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    return "-"


def _log_authorization_decision(
    *,
    request: Request,
    user_id: int,
    permission_id: str,
    required_scope: str,
    decision: str,
) -> None:
    logger.info(
        (
            "event=api_authorization_decision request_id=%s user_id=%s permission_id=%s "
            "required_scope=%s decision=%s method=%s path=%s route=%s"
        ),
        _get_request_id(request),
        user_id,
        permission_id,
        required_scope,
        decision,
        request.method,
        request.url.path,
        _get_route_template(request),
    )


def require_permission(
    permission_id: str,
    *,
    required_scope: str = PermissionScope.ANY,
    resource_context_dependency: PermissionContextProvider = build_default_permission_context,
    conditional_policy_dependency: ConditionalPermissionPolicyDependency = allow_conditional_permission_policy,
) -> PermissionPolicyDependency:
    normalized_required_scope = normalize_permission_scope(required_scope)

    async def dependency(
        current_user: CurrentActiveUserDependency,
        auth_service: AuthServiceDependency,
        request: Request,
        resource_context: Annotated[PermissionResourceContext, Depends(resource_context_dependency)],
        conditional_policy_allowed: Annotated[bool, Depends(conditional_policy_dependency)],
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
            _log_authorization_decision(
                request=request,
                user_id=current_user.id,
                permission_id=permission_id,
                required_scope=normalized_required_scope,
                decision="deny",
            )
            raise ForbiddenError(
                message=f"Missing required permission: {permission_id}",
                details={"permission_id": permission_id},
            )
        if not conditional_policy_allowed:
            _log_authorization_decision(
                request=request,
                user_id=current_user.id,
                permission_id=permission_id,
                required_scope=normalized_required_scope,
                decision="deny",
            )
            raise ForbiddenError(
                message=f"Conditional policy denied access: {permission_id}",
                details={
                    "permission_id": permission_id,
                    "authorization_stage": "conditional_policy",
                },
            )

        _log_authorization_decision(
            request=request,
            user_id=current_user.id,
            permission_id=permission_id,
            required_scope=normalized_required_scope,
            decision="allow",
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
    ) -> CurrentPrincipal:
        return current_user

    return dependency
