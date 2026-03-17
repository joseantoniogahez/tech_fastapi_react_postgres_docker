import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from pydantic import ValidationError

from app.core.common.openapi import normalize_generated_openapi_schema
from app.core.config.settings import ApiSettings, AuthSettings
from app.core.errors.setup.handlers import REQUEST_ID_HEADER, configure_exception_handlers
from app.core.setup.cors import configure_cors
from app.core.setup.routers import configure_routers


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


def configure_request_context_middleware(app: FastAPI) -> None:
    logger = logging.getLogger("app.http")

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, "").strip() or uuid4().hex
        request.state.request_id = request_id

        started_at = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started_at) * 1000
            logger.log(
                logging.ERROR,
                "event=api_request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                500,
                duration_ms,
            )
            raise
        duration_ms = (perf_counter() - started_at) * 1000

        response.headers.setdefault(REQUEST_ID_HEADER, request_id)

        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING

        logger.log(
            log_level,
            "event=api_request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def configure_openapi(app: FastAPI) -> None:
    def custom_openapi() -> dict[str, object]:
        if app.openapi_schema is not None:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            summary=app.summary,
            description=app.description,
            routes=app.routes,
            webhooks=app.webhooks.routes,
            tags=app.openapi_tags,
            servers=app.servers,
            terms_of_service=app.terms_of_service,
            contact=app.contact,
            license_info=app.license_info,
            separate_input_output_schemas=app.separate_input_output_schemas,
            external_docs=app.openapi_external_docs,
        )
        app.openapi_schema = normalize_generated_openapi_schema(openapi_schema)
        return app.openapi_schema

    app.openapi = custom_openapi


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
    configure_request_context_middleware(app)
    configure_cors(app, api_settings)
    configure_exception_handlers(app)
    configure_routers(app)
    configure_openapi(app)

    return app
