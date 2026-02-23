import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.const.settings import ApiSettings
from app.dependencies.providers import get_db_session
from app.factory import app_lifespan, configure_logging
from app.main import app
from app.routers import ROUTER_MODULES
from app.setup.cors import configure_cors
from app.setup.routers import _load_router, get_registered_routers


def test_configure_logging_warns_on_invalid_level() -> None:
    with patch("app.factory.logging.getLogger") as get_logger:
        configure_logging(ApiSettings(LOG_LEVEL="invalid"))

    get_logger.return_value.warning.assert_called_once_with(
        "Invalid LOG_LEVEL '%s'. Falling back to INFO.",
        "invalid",
    )


def test_app_lifespan_logs_startup_and_shutdown() -> None:
    logger = MagicMock()

    async def run_lifespan() -> None:
        async with app_lifespan(FastAPI()):
            pass

    with patch("app.factory.logging.getLogger", return_value=logger):
        asyncio.run(run_lifespan())

    logger.info.assert_has_calls(
        [
            call("Backend startup."),
            call("Backend shutdown."),
        ]
    )


def test_get_registered_routers_loads_catalog_modules() -> None:
    routers = get_registered_routers()
    assert len(routers) == len(ROUTER_MODULES)
    assert all(isinstance(router, APIRouter) for router in routers)


def test_app_registers_routes_from_dynamic_catalog() -> None:
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    expected_paths = {
        "/health",
        "/token",
        "/users/me",
        "/users/register",
        "/books/",
        "/authors/",
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


def test_get_db_session_yields_session_from_async_session_database() -> None:
    events: list[str] = []
    expected_session = object()

    class _SessionContextManager:
        async def __aenter__(self) -> object:
            events.append("enter")
            return expected_session

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            events.append("exit")

    async def run_test() -> None:
        with patch("app.dependencies.providers.AsyncSessionDatabase", return_value=_SessionContextManager()) as factory:
            generator = get_db_session()
            session = await anext(generator)
            assert session is expected_session

            with pytest.raises(StopAsyncIteration):
                await anext(generator)

            factory.assert_called_once_with()

    asyncio.run(run_test())
    assert events == ["enter", "exit"]


def test_get_registered_routers_supports_fully_qualified_module_names() -> None:
    with patch("app.setup.routers.ROUTER_MODULES", ["app.routers.health"]):
        routers = get_registered_routers()

    assert len(routers) == 1
    assert isinstance(routers[0], APIRouter)


def test_load_router_raises_for_invalid_router_export() -> None:
    invalid_module = SimpleNamespace(router="not-an-api-router")

    with patch("app.setup.routers.import_module", return_value=invalid_module):
        with pytest.raises(RuntimeError) as exc_info:
            _load_router("invalid_module")

    assert "app.routers.invalid_module" in str(exc_info.value)
    assert "APIRouter" in str(exc_info.value)
