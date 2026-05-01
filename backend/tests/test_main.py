import asyncio
import logging
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from fastapi import APIRouter, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.testclient import TestClient

from app.core.common.openapi import normalize_generated_openapi_schema
from app.core.config.settings import ApiSettings, AuthSettings
from app.core.errors.setup.handlers import REQUEST_ID_HEADER, configure_exception_handlers
from app.core.setup.cors import configure_cors
from app.core.setup.dependencies import create_async_session, get_db_session, get_unit_of_work
from app.core.setup.factory import (
    app_lifespan,
    configure_logging,
    configure_request_context_middleware,
    create_app,
    validate_auth_settings,
)
from app.core.setup.routers import ROUTER_MODULES, _load_router, get_registered_routers
from app.main import app


def test_configure_logging_warns_on_invalid_level() -> None:
    with patch("app.core.setup.factory.logging.getLogger") as get_logger:
        configure_logging(ApiSettings(LOG_LEVEL="invalid"))

    get_logger.return_value.warning.assert_called_once_with(
        "Invalid LOG_LEVEL '%s'. Falling back to INFO.",
        "invalid",
    )


def test_validate_auth_settings_allows_defaults_outside_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_ALGORITHM", raising=False)
    monkeypatch.delenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
    monkeypatch.delenv("JWT_ISSUER", raising=False)
    monkeypatch.delenv("JWT_AUDIENCE", raising=False)

    validate_auth_settings()


def test_validate_auth_settings_raises_when_jwt_secret_is_missing_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("JWT_ISSUER", "unit-test-issuer")
    monkeypatch.setenv("JWT_AUDIENCE", "unit-test-audience")

    with pytest.raises(RuntimeError) as exc_info:
        validate_auth_settings()

    assert "Invalid JWT settings." in str(exc_info.value)


def test_validate_auth_settings_raises_when_jwt_secret_is_insecure_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("JWT_SECRET_KEY", "local-dev-jwt-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("JWT_ISSUER", "unit-test-issuer")
    monkeypatch.setenv("JWT_AUDIENCE", "unit-test-audience")

    with pytest.raises(RuntimeError) as exc_info:
        validate_auth_settings()

    assert "Invalid JWT settings." in str(exc_info.value)


def test_validate_auth_settings_allows_secure_values_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("JWT_SECRET_KEY", "production-secure-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("JWT_ISSUER", "unit-test-issuer")
    monkeypatch.setenv("JWT_AUDIENCE", "unit-test-audience")

    validate_auth_settings()


def test_auth_settings_validators_for_blank_values() -> None:
    settings = AuthSettings(APP_ENV="   ", JWT_SECRET_KEY="unit-test-secret", JWT_ALGORITHM="HS256")
    assert settings.APP_ENV == "local"

    with pytest.raises(ValidationError):
        AuthSettings(JWT_SECRET_KEY="   ")

    with pytest.raises(ValidationError):
        AuthSettings(JWT_ALGORITHM="   ")

    with pytest.raises(ValidationError):
        AuthSettings(JWT_ISSUER="   ")

    with pytest.raises(ValidationError):
        AuthSettings(JWT_AUDIENCE="   ")


def test_app_lifespan_logs_startup_and_shutdown() -> None:
    logger = MagicMock()

    async def run_lifespan() -> None:
        async with app_lifespan(FastAPI()):
            pass

    with patch("app.core.setup.factory.logging.getLogger", return_value=logger):
        asyncio.run(run_lifespan())

    logger.info.assert_has_calls(
        [
            call("Backend startup."),
            call("Backend shutdown."),
        ]
    )


def test_request_context_middleware_generates_request_id_and_logs_success() -> None:
    logger = MagicMock()
    with patch("app.core.setup.factory.logging.getLogger", return_value=logger):
        test_app = FastAPI()
        configure_request_context_middleware(test_app)

    @test_app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    with TestClient(test_app) as client:
        response = client.get("/ping")

    assert response.status_code == 200
    request_id = response.headers[REQUEST_ID_HEADER]
    assert request_id

    log_call = logger.log.call_args
    assert log_call is not None
    assert log_call.args[0] == logging.INFO
    assert (
        log_call.args[1]
        == "event=api_request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f"
    )
    assert log_call.args[2] == request_id
    assert log_call.args[3] == "GET"
    assert log_call.args[4] == "/ping"
    assert log_call.args[5] == 200
    assert log_call.args[6] >= 0


def test_request_context_middleware_reuses_incoming_request_id_for_errors() -> None:
    logger = MagicMock()
    with patch("app.core.setup.factory.logging.getLogger", return_value=logger):
        test_app = FastAPI()
        configure_request_context_middleware(test_app)
    configure_exception_handlers(test_app)

    @test_app.get("/boom")
    async def boom() -> None:
        raise StarletteHTTPException(status_code=404, detail="Missing")

    with TestClient(test_app) as client:
        response = client.get("/boom", headers={REQUEST_ID_HEADER: "req-123"})

    assert response.status_code == 404
    assert response.headers[REQUEST_ID_HEADER] == "req-123"
    assert response.json()["request_id"] == "req-123"

    log_call = logger.log.call_args
    assert log_call is not None
    assert log_call.args[0] == logging.WARNING
    assert log_call.args[2] == "req-123"
    assert log_call.args[3] == "GET"
    assert log_call.args[4] == "/boom"
    assert log_call.args[5] == 404


def test_request_context_middleware_logs_server_errors_and_explicit_500_at_error_level() -> None:
    logger = MagicMock()
    with patch("app.core.setup.factory.logging.getLogger", return_value=logger):
        test_app = FastAPI()
        configure_request_context_middleware(test_app)
    configure_exception_handlers(test_app)

    @test_app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("boom")

    @test_app.get("/status-500")
    async def status_500() -> Response:
        return Response(status_code=500)

    with TestClient(test_app, raise_server_exceptions=False) as client:
        crash_response = client.get("/crash")
        explicit_500_response = client.get("/status-500")

    assert crash_response.status_code == 500
    crash_request_id = crash_response.headers[REQUEST_ID_HEADER]
    assert crash_response.json()["request_id"] == crash_request_id

    assert explicit_500_response.status_code == 500

    error_logs = [
        call_args
        for call_args in logger.log.call_args_list
        if call_args.args[0] == logging.ERROR and call_args.args[5] == 500
    ]
    assert len(error_logs) >= 2
    assert any(call_args.args[4] == "/crash" for call_args in error_logs)
    assert any(call_args.args[4] == "/status-500" for call_args in error_logs)


def test_generated_openapi_matches_normalized_validation_contracts() -> None:
    test_app = create_app(ApiSettings())
    openapi_schema = test_app.openapi()

    register_responses = openapi_schema["paths"]["/v1/users/register"]["post"]["responses"]
    update_me_responses = openapi_schema["paths"]["/v1/users/me"]["patch"]["responses"]
    role_permission_operation = openapi_schema["paths"]["/v1/rbac/roles/{role_id}/permissions/{permission_id}"]["put"]
    error_schema = register_responses["400"]["content"]["application/json"]["schema"]
    scope_request_schema = openapi_schema["components"]["schemas"]["SetRolePermissionRequest"]

    assert "422" not in register_responses
    assert "422" not in update_me_responses
    assert "422" not in role_permission_operation["responses"]
    assert "HTTPValidationError" not in openapi_schema["components"]["schemas"]
    assert "ValidationError" not in openapi_schema["components"]["schemas"]

    assert "request_id" in error_schema["required"]
    assert error_schema["properties"]["request_id"]["type"] == "string"
    assert REQUEST_ID_HEADER in register_responses["400"]["headers"]
    assert register_responses["400"]["headers"][REQUEST_ID_HEADER]["schema"]["type"] == "string"

    assert set(scope_request_schema["required"]) == {"scope"}
    assert "default" not in scope_request_schema["properties"]["scope"]


def test_normalize_generated_openapi_schema_handles_non_dict_paths_and_operations() -> None:
    openapi_schema = {
        "paths": {
            "/invalid-path-item": "not-a-dict",
            "/users": {
                "get": "not-a-dict",
                "post": {
                    "responses": {
                        "200": {"description": "ok"},
                        "422": {"description": "validation error"},
                        422: {"description": "validation error int key"},
                    }
                },
            },
        },
        "components": {
            "schemas": {
                "HTTPValidationError": {"type": "object"},
                "ValidationError": {"type": "object"},
            }
        },
    }

    normalized = normalize_generated_openapi_schema(openapi_schema)

    responses = normalized["paths"]["/users"]["post"]["responses"]
    assert "422" not in responses
    assert 422 not in responses
    assert "HTTPValidationError" not in normalized["components"]["schemas"]
    assert "ValidationError" not in normalized["components"]["schemas"]


def test_normalize_generated_openapi_schema_keeps_referenced_components() -> None:
    openapi_schema = {
        "paths": {},
        "components": {
            "schemas": {
                "HTTPValidationError": {"type": "object"},
                "ReferencedSchema": {
                    "type": "object",
                    "properties": {
                        "error": {"$ref": "#/components/schemas/HTTPValidationError"},
                    },
                },
            }
        },
    }

    normalized = normalize_generated_openapi_schema(openapi_schema)

    assert "HTTPValidationError" in normalized["components"]["schemas"]


def test_normalize_generated_openapi_schema_tolerates_missing_component_mappings() -> None:
    schema_with_non_mapping_components: dict[str, Any] = {"paths": {}, "components": None}
    schema_with_missing_named_schema: dict[str, Any] = {"paths": {}, "components": {"schemas": {}}}

    normalized_non_mapping = normalize_generated_openapi_schema(schema_with_non_mapping_components)
    normalized_missing_schema = normalize_generated_openapi_schema(schema_with_missing_named_schema)

    assert normalized_non_mapping is schema_with_non_mapping_components
    assert normalized_missing_schema is schema_with_missing_named_schema


def test_create_app_openapi_returns_cached_schema_without_regenerating() -> None:
    test_app = create_app(ApiSettings())
    expected_schema: dict[str, Any] = {"openapi": "3.1.0", "paths": {}}
    test_app.openapi_schema = expected_schema

    with patch("app.core.setup.factory.get_openapi", side_effect=AssertionError("get_openapi should not run")):
        assert test_app.openapi() is expected_schema


def test_get_registered_routers_loads_catalog_modules_and_supports_fqcn() -> None:
    routers = get_registered_routers()
    assert len(routers) == len(ROUTER_MODULES)
    assert all(isinstance(router, APIRouter) for router in routers)

    with patch("app.core.setup.routers.ROUTER_MODULES", ["app.features.health.router"]):
        fqcn_routers = get_registered_routers()

    assert len(fqcn_routers) == 1
    assert isinstance(fqcn_routers[0], APIRouter)


def test_app_registers_routes_from_dynamic_catalog() -> None:
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    expected_paths = {
        "/v1/health",
        "/v1/token",
        "/v1/users/me",
        "/v1/users/register",
        "/v1/rbac/roles",
        "/v1/rbac/permissions",
        "/v1/rbac/users",
        "/v1/rbac/users/{user_id}",
        "/v1/rbac/users/{user_id}/roles",
        "/v1/rbac/roles/{role_id}/users",
    }
    assert expected_paths.issubset(paths)


def test_configure_cors_adds_cors_middleware_when_origins_are_provided() -> None:
    test_app = MagicMock(spec=FastAPI)
    settings = ApiSettings(API_CORS_ORIGINS="http://localhost:3000, https://example.com")

    configure_cors(test_app, settings)

    test_app.add_middleware.assert_called_once_with(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://example.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def test_get_db_session_yields_session_from_create_async_session() -> None:
    events: list[str] = []
    expected_session = object()

    class _SessionContextManager:
        async def __aenter__(self) -> object:
            events.append("enter")
            return expected_session

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            events.append("exit")

    async def run_test() -> None:
        with patch(
            "app.core.setup.dependencies.create_async_session", return_value=_SessionContextManager()
        ) as factory:
            generator = get_db_session()
            session = await anext(generator)
            assert session is expected_session

            with pytest.raises(StopAsyncIteration):
                await anext(generator)

            factory.assert_called_once_with()

    asyncio.run(run_test())
    assert events == ["enter", "exit"]


def test_create_async_session_calls_lazy_factory() -> None:
    expected_session_context = object()
    factory = MagicMock(return_value=expected_session_context)

    with patch("app.core.setup.dependencies.get_async_session_factory", return_value=factory) as get_factory:
        result = create_async_session()

    assert result is expected_session_context
    get_factory.assert_called_once_with()
    factory.assert_called_once_with()


def test_get_db_session_rolls_back_when_exception_is_raised_after_yield() -> None:
    events: list[str] = []
    session = MagicMock()
    session.rollback = AsyncMock()

    class _SessionContextManager:
        async def __aenter__(self) -> object:
            events.append("enter")
            return session

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            events.append("exit")

    async def run_test() -> None:
        with patch("app.core.setup.dependencies.create_async_session", return_value=_SessionContextManager()):
            generator = get_db_session()
            yielded_session = await anext(generator)
            assert yielded_session is session

            with pytest.raises(RuntimeError, match="boom"):
                await generator.athrow(RuntimeError("boom"))

    asyncio.run(run_test())
    session.rollback.assert_awaited_once_with()
    assert events == ["enter", "exit"]


def test_get_unit_of_work_returns_repository_unit_of_work() -> None:
    session = object()
    expected_uow = object()

    async def run_test() -> None:
        with patch("app.core.setup.dependencies.UnitOfWork", return_value=expected_uow) as unit_of_work:
            result = await get_unit_of_work(session)  # type: ignore[arg-type]

        assert result is expected_uow
        unit_of_work.assert_called_once_with(session=session)

    asyncio.run(run_test())


def test_load_router_raises_for_invalid_router_export() -> None:
    invalid_module = SimpleNamespace(router="not-an-api-router")

    with (
        patch("app.core.setup.routers.import_module", return_value=invalid_module),
        pytest.raises(RuntimeError) as exc_info,
    ):
        _load_router("invalid_module")

    assert "invalid_module" in str(exc_info.value)
    assert "APIRouter" in str(exc_info.value)
