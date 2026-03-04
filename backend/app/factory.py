import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from app.const.settings import ApiSettings, AuthSettings
from app.exceptions.setup.handlers import configure_exception_handlers
from app.setup.cors import configure_cors
from app.setup.routers import configure_routers


def configure_logging(settings: ApiSettings) -> None:
    level_name = settings.LOG_LEVEL.upper()
    level = logging._nameToLevel.get(level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )
    if level_name not in logging._nameToLevel:
        logging.getLogger(__name__).warning("Invalid LOG_LEVEL '%s'. Falling back to INFO.", settings.LOG_LEVEL)


def validate_auth_settings() -> None:
    try:
        AuthSettings()
    except ValidationError as exc:
        raise RuntimeError(
            "Invalid JWT settings. "
            "Set APP_ENV=prod with explicit JWT_SECRET_KEY, JWT_ALGORITHM and JWT_ACCESS_TOKEN_EXPIRE_MINUTES. "
            "Non-production environments can use local defaults."
        ) from exc


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = logging.getLogger("app.lifecycle")
    validate_auth_settings()
    logger.info("Backend startup.")
    yield
    logger.info("Backend shutdown.")


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    api_settings = settings or ApiSettings()
    configure_logging(api_settings)

    app = FastAPI(root_path=api_settings.API_PATH, lifespan=app_lifespan)
    configure_cors(app, api_settings)
    configure_exception_handlers(app)
    configure_routers(app)

    return app
