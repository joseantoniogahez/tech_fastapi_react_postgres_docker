import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.const.settings import ApiSettings
from app.routers import author, book, health


def _configure_logging(settings: ApiSettings) -> None:
    level_name = settings.LOG_LEVEL.upper()
    level = logging._nameToLevel.get(level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )
    if level_name not in logging._nameToLevel:
        logging.getLogger(__name__).warning("Invalid LOG_LEVEL '%s'. Falling back to INFO.", settings.LOG_LEVEL)


@asynccontextmanager
async def _app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = logging.getLogger("app.lifecycle")
    logger.info("Backend startup.")
    yield
    logger.info("Backend shutdown.")


def _attach_app_cors(app: FastAPI, settings: ApiSettings) -> None:
    origins = settings.API_CORS_ORIGINS.split(",")
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


def _attach_app_routers(app: FastAPI) -> None:
    app.include_router(health.router)
    app.include_router(book.router)
    app.include_router(author.router)


def create_app() -> FastAPI:
    settings = ApiSettings()
    _configure_logging(settings)
    app = FastAPI(root_path=settings.API_PATH, lifespan=_app_lifespan)
    _attach_app_cors(app, settings)
    _attach_app_routers(app)
    return app


app = create_app()
