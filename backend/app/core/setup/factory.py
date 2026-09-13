import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from pydantic import ValidationError

from app.core.common.observability import resolve_request_id, sanitize_log_text
from app.core.common.openapi import normalize_generated_openapi_schema
from app.core.config.settings import ApiSettings, AuthSettings, RateLimitSettings
from app.core.errors.setup.handlers import REQUEST_ID_HEADER, configure_exception_handlers
from app.core.rate_limit import build_rate_limiter
from app.core.setup.cors import configure_cors
from app.core.setup.routers import configure_routers


def _build_openapi_schema(app: FastAPI) -> dict[str, Any]:
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
    return normalize_generated_openapi_schema(openapi_schema)


class _NormalizedOpenAPIFastAPI(FastAPI):
    def openapi(self) -> dict[str, Any]:
        if self.openapi_schema is not None:
            return self.openapi_schema

        self.openapi_schema = _build_openapi_schema(self)
        return self.openapi_schema


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
        request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        client_ip = sanitize_log_text(request.client.host if request.client is not None else "-")
        method = sanitize_log_text(request.method)
        path = sanitize_log_text(request.url.path)

        started_at = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - started_at) * 1000
            logger.log(
                logging.ERROR,
                "event=api_request_completed request_id=%s client_ip=%s method=%s path=%s status_code=%s duration_ms=%.2f",
                request_id,
                client_ip,
                method,
                path,
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
            "event=api_request_completed request_id=%s client_ip=%s method=%s path=%s status_code=%s duration_ms=%.2f",
            request_id,
            client_ip,
            method,
            path,
            response.status_code,
            duration_ms,
        )
        return response


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = logging.getLogger("app.lifecycle")
    validate_auth_settings()
    rate_limit_settings = getattr(app.state, "rate_limit_settings", RateLimitSettings())
    rate_limiter = build_rate_limiter(rate_limit_settings)
    app.state.rate_limiter = rate_limiter
    logger.info("Backend startup.")
    try:
        yield
    finally:
        await rate_limiter.aclose()
        logger.info("Backend shutdown.")


def create_app(
    settings: ApiSettings | None = None,
    rate_limit_settings: RateLimitSettings | None = None,
) -> FastAPI:
    api_settings = settings or ApiSettings()
    limiter_settings = rate_limit_settings or RateLimitSettings(APP_ENV=api_settings.APP_ENV)
    configure_logging(api_settings)

    docs_url = "/docs" if api_settings.openapi_enabled else None
    redoc_url = "/redoc" if api_settings.openapi_enabled else None
    openapi_url = "/openapi.json" if api_settings.openapi_enabled else None
    app = _NormalizedOpenAPIFastAPI(
        root_path=api_settings.API_PATH,
        lifespan=app_lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.state.rate_limit_settings = limiter_settings
    configure_request_context_middleware(app)
    configure_cors(app, api_settings)
    configure_exception_handlers(app)
    configure_routers(app)

    return app
