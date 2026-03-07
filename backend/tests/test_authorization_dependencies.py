import asyncio
from unittest.mock import patch

from starlette.requests import Request

from app.core.authorization import PermissionId, PermissionScope
from app.core.authorization.dependencies import (
    _log_authorization_decision,
    build_current_tenant_permission_context,
    build_current_user_permission_context,
    build_default_permission_context,
)
from app.features.auth.principal import CurrentPrincipal


def _build_user(*, user_id: int, tenant_id: int | None) -> CurrentPrincipal:
    return CurrentPrincipal(
        id=user_id,
        username="dependency-user",
        disabled=False,
        tenant_id=tenant_id,
    )


def _request(path: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "http_version": "1.1",
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
    )


def test_build_default_permission_context_returns_empty_context() -> None:
    async def run_test() -> None:
        context = await build_default_permission_context()

        assert context.owner_user_id is None
        assert context.tenant_id is None

    asyncio.run(run_test())


def test_build_current_user_permission_context_maps_owner_and_tenant() -> None:
    current_user = _build_user(user_id=7, tenant_id=11)

    async def run_test() -> None:
        context = await build_current_user_permission_context(current_user)

        assert context.owner_user_id == 7
        assert context.tenant_id == 11

    asyncio.run(run_test())


def test_build_current_tenant_permission_context_maps_tenant_only() -> None:
    current_user = _build_user(user_id=9, tenant_id=22)

    async def run_test() -> None:
        context = await build_current_tenant_permission_context(current_user)

        assert context.owner_user_id is None
        assert context.tenant_id == 22

    asyncio.run(run_test())


def test_log_authorization_decision_falls_back_when_request_context_is_missing() -> None:
    request = _request("/scope/fallback/42")

    with patch("app.core.authorization.dependencies.logger") as authz_logger:
        _log_authorization_decision(
            request=request,
            user_id=7,
            permission_id=PermissionId.ROLE_PERMISSION_MANAGE,
            required_scope=PermissionScope.ANY,
            decision="allow",
        )

    authz_logger.info.assert_called_once()
    log_call = authz_logger.info.call_args
    assert log_call is not None
    assert (
        log_call.args[0]
        == "event=api_authorization_decision request_id=%s user_id=%s permission_id=%s required_scope=%s decision=%s method=%s path=%s route=%s"
    )
    assert log_call.args[1] == "-"
    assert log_call.args[7] == "/scope/fallback/42"
    assert log_call.args[8] == "/scope/fallback/42"
