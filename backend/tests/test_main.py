import asyncio
from unittest.mock import MagicMock, call, patch

from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute

from app.const.settings import ApiSettings
from app.factory import app_lifespan, configure_logging
from app.main import app
from app.routers import ROUTER_MODULES
from app.setup.routers import get_registered_routers


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
