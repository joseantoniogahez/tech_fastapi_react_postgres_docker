import asyncio
from unittest.mock import MagicMock, call, patch

from fastapi import FastAPI

from app.const.settings import ApiSettings
from app.main import _app_lifespan, _configure_logging


def test_configure_logging_warns_on_invalid_level() -> None:
    with patch("app.main.logging.getLogger") as get_logger:
        _configure_logging(ApiSettings(LOG_LEVEL="invalid"))

    get_logger.return_value.warning.assert_called_once_with(
        "Invalid LOG_LEVEL '%s'. Falling back to INFO.",
        "invalid",
    )


def test_app_lifespan_logs_startup_and_shutdown() -> None:
    logger = MagicMock()

    async def run_lifespan() -> None:
        async with _app_lifespan(FastAPI()):
            pass

    with patch("app.main.logging.getLogger", return_value=logger):
        asyncio.run(run_lifespan())

    logger.info.assert_has_calls(
        [
            call("Backend startup."),
            call("Backend shutdown."),
        ]
    )
