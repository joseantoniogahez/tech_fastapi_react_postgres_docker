from http import HTTPStatus
from typing import Annotated, Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import Depends, FastAPI
from starlette.testclient import TestClient

from app.authorization import PermissionId, PermissionScope
from app.const.settings import AuthSettings
from app.dependencies.authentication import get_current_active_user
from app.dependencies.authorization import PermissionResourceContext, require_permission
from app.dependencies.services import get_auth_service
from app.exceptions.setup.handlers import configure_exception_handlers
from app.factory import configure_request_context_middleware
from app.models.user import User
from app.services.auth import AuthService
from utils.testing_support.api_assertions import assert_error_response


def _build_scoped_auth_service(
    granted_scope: str | None,
    *,
    permission_scope_cache: dict[tuple[int, str], str | None] | None = None,
) -> AuthService:
    repository = MagicMock()
    repository.get_by_username = AsyncMock()
    repository.username_exists = AsyncMock(return_value=False)
    repository.create = AsyncMock()
    repository.update = AsyncMock()
    repository.get_user_permission_scope = AsyncMock(return_value=granted_scope)
    repository.user_has_permission = AsyncMock()

    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)
    settings = AuthSettings(
        JWT_SECRET_KEY="unit-test-secret",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
    )
    return AuthService(
        auth_repository=repository,
        unit_of_work=unit_of_work,
        auth_settings=settings,
        permission_scope_cache=permission_scope_cache,
    )


def _build_scoped_test_app() -> FastAPI:
    app = FastAPI()
    configure_request_context_middleware(app)
    configure_exception_handlers(app)

    async def owner_context(target_user_id: int) -> PermissionResourceContext:
        return PermissionResourceContext(owner_user_id=target_user_id)

    async def tenant_context(target_tenant_id: int) -> PermissionResourceContext:
        return PermissionResourceContext(tenant_id=target_tenant_id)

    @app.get("/scope/own/{target_user_id}")
    async def own_scope_route(
        _: Annotated[
            None,
            Depends(
                require_permission(
                    PermissionId.BOOK_UPDATE,
                    required_scope=PermissionScope.OWN,
                    resource_context_dependency=owner_context,
                )
            ),
        ],
    ) -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/scope/tenant/{target_tenant_id}")
    async def tenant_scope_route(
        _: Annotated[
            None,
            Depends(
                require_permission(
                    PermissionId.BOOK_UPDATE,
                    required_scope=PermissionScope.TENANT,
                    resource_context_dependency=tenant_context,
                )
            ),
        ],
    ) -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/scope/any")
    async def any_scope_route(
        _: Annotated[
            None,
            Depends(require_permission(PermissionId.BOOK_UPDATE, required_scope=PermissionScope.ANY)),
        ],
    ) -> dict[str, str]:
        return {"status": "ok"}

    first_permission_check = require_permission(PermissionId.BOOK_UPDATE, required_scope=PermissionScope.ANY)
    second_permission_check = require_permission(PermissionId.BOOK_UPDATE, required_scope=PermissionScope.ANY)

    @app.get("/scope/multi")
    async def multi_scope_route(
        _: Annotated[None, Depends(first_permission_check)],
        __: Annotated[None, Depends(second_permission_check)],
    ) -> dict[str, str]:
        return {"status": "ok"}

    return app


def _request_with_scope(
    path: str,
    *,
    granted_scope: str | None,
    current_user_id: int = 10,
    current_user_tenant_id: int | None = 7,
) -> Any:
    app = _build_scoped_test_app()
    current_user = User(
        id=current_user_id,
        username="scope-user",
        hashed_password="hash",
        disabled=False,
        tenant_id=current_user_tenant_id,
    )
    auth_service = _build_scoped_auth_service(granted_scope)

    async def override_current_active_user() -> User:
        return current_user

    async def override_auth_service() -> AuthService:
        return auth_service

    app.dependency_overrides[get_current_active_user] = override_current_active_user
    app.dependency_overrides[get_auth_service] = override_auth_service
    try:
        with TestClient(app) as client:
            return client.get(path)
    finally:
        app.dependency_overrides.clear()


def test_scoped_authorization_allows_own_scope_for_self_service() -> None:
    response = _request_with_scope("/scope/own/10", granted_scope=PermissionScope.OWN)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


def test_scoped_authorization_denies_own_scope_for_other_owner() -> None:
    response = _request_with_scope("/scope/own/11", granted_scope=PermissionScope.OWN)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.BOOK_UPDATE}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.BOOK_UPDATE},
    )


def test_scoped_authorization_allows_tenant_scope_for_matching_tenant() -> None:
    response = _request_with_scope("/scope/tenant/7", granted_scope=PermissionScope.TENANT)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


def test_scoped_authorization_denies_tenant_scope_for_mismatched_tenant() -> None:
    response = _request_with_scope("/scope/tenant/8", granted_scope=PermissionScope.TENANT)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.BOOK_UPDATE}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.BOOK_UPDATE},
    )


def test_scoped_authorization_allows_any_scope_for_global_admin() -> None:
    response = _request_with_scope("/scope/any", granted_scope=PermissionScope.ANY)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


def test_scoped_authorization_denies_non_global_scope_when_any_is_required() -> None:
    response = _request_with_scope("/scope/any", granted_scope=PermissionScope.TENANT)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert_error_response(
        response,
        detail=f"Missing required permission: {PermissionId.BOOK_UPDATE}",
        status_code=HTTPStatus.FORBIDDEN,
        code="forbidden",
        meta={"permission_id": PermissionId.BOOK_UPDATE},
    )


def test_scoped_authorization_logs_allow_decision_event() -> None:
    with patch("app.dependencies.authorization.logger") as authz_logger:
        response = _request_with_scope("/scope/own/10", granted_scope=PermissionScope.OWN)

    assert response.status_code == HTTPStatus.OK
    authz_logger.info.assert_called_once()
    log_call = authz_logger.info.call_args
    assert log_call is not None
    assert (
        log_call.args[0]
        == "event=api_authorization_decision request_id=%s user_id=%s permission_id=%s required_scope=%s decision=%s method=%s path=%s route=%s"
    )
    assert isinstance(log_call.args[1], str) and log_call.args[1]
    assert log_call.args[2] == 10
    assert log_call.args[3] == PermissionId.BOOK_UPDATE
    assert log_call.args[4] == PermissionScope.OWN
    assert log_call.args[5] == "allow"
    assert log_call.args[6] == "GET"
    assert log_call.args[7] == "/scope/own/10"
    assert log_call.args[8] == "/scope/own/{target_user_id}"


def test_scoped_authorization_logs_deny_decision_event() -> None:
    with patch("app.dependencies.authorization.logger") as authz_logger:
        response = _request_with_scope("/scope/tenant/8", granted_scope=PermissionScope.TENANT)

    assert response.status_code == HTTPStatus.FORBIDDEN
    authz_logger.info.assert_called_once()
    log_call = authz_logger.info.call_args
    assert log_call is not None
    assert (
        log_call.args[0]
        == "event=api_authorization_decision request_id=%s user_id=%s permission_id=%s required_scope=%s decision=%s method=%s path=%s route=%s"
    )
    assert isinstance(log_call.args[1], str) and log_call.args[1]
    assert log_call.args[2] == 10
    assert log_call.args[3] == PermissionId.BOOK_UPDATE
    assert log_call.args[4] == PermissionScope.TENANT
    assert log_call.args[5] == "deny"
    assert log_call.args[6] == "GET"
    assert log_call.args[7] == "/scope/tenant/8"
    assert log_call.args[8] == "/scope/tenant/{target_tenant_id}"


def test_scoped_authorization_reuses_permission_lookup_within_request() -> None:
    app = _build_scoped_test_app()
    current_user = User(
        id=10,
        username="scope-user",
        hashed_password="hash",
        disabled=False,
        tenant_id=7,
    )
    auth_service = _build_scoped_auth_service(
        PermissionScope.ANY,
        permission_scope_cache={},
    )

    async def override_current_active_user() -> User:
        return current_user

    async def override_auth_service() -> AuthService:
        return auth_service

    app.dependency_overrides[get_current_active_user] = override_current_active_user
    app.dependency_overrides[get_auth_service] = override_auth_service
    try:
        with TestClient(app) as client:
            response = client.get("/scope/multi")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == HTTPStatus.OK
    repository = cast(MagicMock, auth_service.auth_repository)
    repository.get_user_permission_scope.assert_awaited_once_with(
        user_id=10,
        permission_id=PermissionId.BOOK_UPDATE,
    )
