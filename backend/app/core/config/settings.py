import os
import re
from ipaddress import ip_address
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings

_APP_ENV_ALIASES = {
    "dev": "development",
    "prod": "production",
}
_APP_ENV_VALUES = {"local", "test", "development", "staging", "production"}
_PRODUCTION_ENV_VALUES = {"staging", "production"}
_DNS_HOST_PATTERN = re.compile(
    r"^(?:localhost|(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*)$"
)


def normalize_app_env(value: str) -> str:
    normalized = value.strip().lower() or "local"
    normalized = _APP_ENV_ALIASES.get(normalized, normalized)
    if normalized not in _APP_ENV_VALUES:
        allowed = ", ".join(sorted(_APP_ENV_VALUES | set(_APP_ENV_ALIASES)))
        raise ValueError(f"APP_ENV must be one of: {allowed}.")
    return normalized


def _canonical_http_origin(value: str) -> str:
    if value == "*":
        raise ValueError("API_CORS_ORIGINS must contain explicit browser origins.")
    if "?" in value or "#" in value:
        raise ValueError("API_CORS_ORIGINS must not contain a query or fragment.")

    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("API_CORS_ORIGINS must contain HTTP(S) origins.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("API_CORS_ORIGINS must not contain credentials.")
    if parsed.path not in {"", "/"}:
        raise ValueError("API_CORS_ORIGINS must not contain paths.")

    host = parsed.hostname
    if host is None or any(ord(character) < 33 or ord(character) == 127 for character in host):
        raise ValueError("API_CORS_ORIGINS contains an invalid host.")
    try:
        ip_address(host)
    except ValueError:
        if _DNS_HOST_PATTERN.fullmatch(host.lower()) is None:
            raise ValueError("API_CORS_ORIGINS contains an invalid host.") from None

    try:
        port = parsed.port
    except ValueError:
        raise ValueError("API_CORS_ORIGINS contains an invalid port.") from None

    normalized_host = f"[{host.lower()}]" if ":" in host else host.lower()
    default_port = 80 if parsed.scheme.lower() == "http" else 443
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{parsed.scheme.lower()}://{normalized_host}{port_suffix}"


class ApiSettings(BaseSettings):
    _OPENAPI_ENV_VALUES: ClassVar[set[str]] = {"local", "test", "development"}

    APP_ENV: str = "local"
    API_PATH: str = ""
    API_CORS_ORIGINS: str = ""
    LOG_LEVEL: str = "WARNING"

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        return normalize_app_env(value)

    @field_validator("API_CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins: list[str] = []
        for raw_origin in value.split(","):
            candidate = raw_origin.strip()
            if not candidate:
                continue
            origin = _canonical_http_origin(candidate)
            if origin not in origins:
                origins.append(origin)
        return ",".join(origins)

    @property
    def cors_origins(self) -> list[str]:
        return [origin for origin in self.API_CORS_ORIGINS.split(",") if origin]

    @property
    def openapi_enabled(self) -> bool:
        return self.APP_ENV in self._OPENAPI_ENV_VALUES


class ReadinessSettings(BaseSettings):
    READINESS_TIMEOUT_SECONDS: float = Field(2.0, gt=0, le=30)
    READINESS_MAX_CONCURRENCY: int = Field(4, ge=1, le=32)


class RateLimitSettings(BaseSettings):
    _PRODUCTION_ENV_VALUES: ClassVar[set[str]] = _PRODUCTION_ENV_VALUES
    _PRODUCTION_REQUIRED_FIELDS: ClassVar[tuple[str, ...]] = (
        "RATE_LIMIT_ENABLED",
        "RATE_LIMIT_STORAGE",
        "RATE_LIMIT_LOGIN",
        "RATE_LIMIT_REGISTER",
        "RATE_LIMIT_WINDOW_SECONDS",
        "REDIS_URL",
    )

    APP_ENV: str = "local"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE: str = "memory"
    RATE_LIMIT_LOGIN: int = Field(10, gt=0, le=100_000)
    RATE_LIMIT_REGISTER: int = Field(5, gt=0, le=100_000)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(60, gt=0, le=86_400)
    RATE_LIMIT_NAMESPACE: str = "foundation:rate-limit:v1"
    REDIS_URL: str | None = None
    REDIS_PASSWORD: SecretStr | None = None
    REDIS_PASSWORD_FILE: Path | None = None
    REDIS_ALLOW_PLAINTEXT: bool = False
    REDIS_TIMEOUT_SECONDS: float = Field(2.0, gt=0, le=30)

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        return normalize_app_env(value)

    @field_validator("RATE_LIMIT_STORAGE")
    @classmethod
    def validate_storage(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"memory", "redis"}:
            raise ValueError("RATE_LIMIT_STORAGE must be memory or redis.")
        return normalized

    @field_validator("RATE_LIMIT_NAMESPACE")
    @classmethod
    def validate_namespace(cls, value: str) -> str:
        normalized = value.strip().lower()
        if re.fullmatch(r"[a-z][a-z0-9:-]{2,63}", normalized) is None:
            raise ValueError("RATE_LIMIT_NAMESPACE must be a neutral lowercase namespace.")
        return normalized

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        parsed = urlsplit(normalized)
        if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
            raise ValueError("REDIS_URL must use redis:// or rediss:// with a host.")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("REDIS_URL must not contain credentials; use REDIS_PASSWORD.")
        if parsed.query or parsed.fragment:
            raise ValueError("REDIS_URL must not contain a query or fragment.")
        if parsed.path not in {"", "/"}:
            database = parsed.path.removeprefix("/")
            if not database.isdigit():
                raise ValueError("REDIS_URL path must be a numeric database index.")
        try:
            _ = parsed.port
        except ValueError:
            raise ValueError("REDIS_URL contains an invalid port.") from None
        return normalized

    def _field_is_explicit(self, field_name: str) -> bool:
        environment_value = os.getenv(field_name)
        return field_name in self.model_fields_set or (
            environment_value is not None and bool(environment_value.strip())
        )

    def _validate_production_requirements(self) -> None:
        if self.APP_ENV not in self._PRODUCTION_ENV_VALUES:
            return
        missing = [name for name in self._PRODUCTION_REQUIRED_FIELDS if not self._field_is_explicit(name)]
        if missing:
            raise ValueError("Production-like rate limiting requires explicit settings: " + ", ".join(sorted(missing)))
        if not self.RATE_LIMIT_ENABLED:
            raise ValueError("Production-like rate limiting cannot be disabled.")
        if self.RATE_LIMIT_STORAGE != "redis":
            raise ValueError("Production-like rate limiting requires shared Redis storage.")

    def _validate_redis_requirements(self) -> None:
        if self.RATE_LIMIT_STORAGE != "redis":
            return
        if self.REDIS_URL is None:
            raise ValueError("REDIS_URL is required when RATE_LIMIT_STORAGE=redis.")
        if self.REDIS_PASSWORD is None and self.REDIS_PASSWORD_FILE is None:
            raise ValueError("REDIS_PASSWORD or REDIS_PASSWORD_FILE is required when RATE_LIMIT_STORAGE=redis.")
        if self.REDIS_PASSWORD is not None and self.REDIS_PASSWORD_FILE is not None:
            raise ValueError("Configure only one of REDIS_PASSWORD or REDIS_PASSWORD_FILE.")
        if self.REDIS_PASSWORD is not None and not self.REDIS_PASSWORD.get_secret_value():
            raise ValueError("REDIS_PASSWORD cannot be empty.")
        if self.REDIS_PASSWORD_FILE is not None:
            try:
                password_from_file = self.REDIS_PASSWORD_FILE.read_text(encoding="utf-8").strip()
            except OSError:
                raise ValueError("REDIS_PASSWORD_FILE must be a readable secret file.") from None
            if not password_from_file:
                raise ValueError("REDIS_PASSWORD_FILE cannot be empty.")
        if self.REDIS_URL.startswith("redis://") and not self.REDIS_ALLOW_PLAINTEXT:
            raise ValueError("Plaintext Redis requires REDIS_ALLOW_PLAINTEXT=true; otherwise use rediss://.")

    @model_validator(mode="after")
    def validate_rate_limit_topology(self) -> RateLimitSettings:
        self._validate_production_requirements()
        self._validate_redis_requirements()
        return self

    @property
    def uses_shared_store(self) -> bool:
        return self.RATE_LIMIT_ENABLED and self.RATE_LIMIT_STORAGE == "redis"

    def redis_password_value(self) -> str:
        if self.REDIS_PASSWORD is not None:
            return self.REDIS_PASSWORD.get_secret_value()
        if self.REDIS_PASSWORD_FILE is not None:
            return self.REDIS_PASSWORD_FILE.read_text(encoding="utf-8").strip()
        raise RuntimeError("Redis password is not configured.")


class AuthSettings(BaseSettings):
    _INSECURE_SECRET_VALUES: ClassVar[set[str]] = {
        "change-me-in-production",
        "changeme",
        "secret",
        "default",
        "password",
        "local-dev-jwt-secret",
        "local-development-jwt-secret-32-bytes",
    }
    _PRODUCTION_ENV_VALUES: ClassVar[set[str]] = _PRODUCTION_ENV_VALUES
    _JWT_REQUIRED_ENV_VARS: ClassVar[tuple[str, ...]] = (
        "JWT_SECRET_KEY",
        "JWT_ALGORITHM",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        "JWT_ISSUER",
        "JWT_AUDIENCE",
    )

    APP_ENV: str = "local"
    JWT_SECRET_KEY: str = "local-development-jwt-secret-32-bytes"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, gt=0)
    JWT_ISSUER: str = "fastapi-template"
    JWT_AUDIENCE: str = "fastapi-template-api"

    @field_validator("APP_ENV")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        return normalize_app_env(value)

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("JWT_SECRET_KEY cannot be empty.")
        return normalized

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("JWT_ALGORITHM cannot be empty.")
        return normalized

    @field_validator("JWT_ISSUER", "JWT_AUDIENCE")
    @classmethod
    def validate_jwt_identity_claim(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("JWT issuer and audience cannot be empty.")
        return normalized

    @classmethod
    def _is_missing_env_var(cls, name: str) -> bool:
        value = os.getenv(name)
        return value is None or not value.strip()

    @model_validator(mode="after")
    def validate_production_jwt_requirements(self) -> AuthSettings:
        if self.APP_ENV not in self._PRODUCTION_ENV_VALUES:
            return self

        missing = [name for name in self._JWT_REQUIRED_ENV_VARS if self._is_missing_env_var(name)]
        if missing:
            missing_vars = ", ".join(sorted(missing))
            raise ValueError(f"Missing required JWT environment variables for production: {missing_vars}.")

        if self.JWT_SECRET_KEY.lower() in self._INSECURE_SECRET_VALUES:
            raise ValueError("JWT_SECRET_KEY contains an insecure placeholder value.")

        return self


class DatabaseSettings(BaseSettings):
    APP_ENV: str = "local"
    DB_REQUIRE_POSTGRESQL: bool = False
    DB_TYPE: str = "sqlite+aiosqlite"
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: int | None = None
    DB_NAME: str = "app.db"

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        return normalize_app_env(value)

    @field_validator("DB_TYPE")
    @classmethod
    def validate_database_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("DB_TYPE cannot be empty.")
        return normalized

    @model_validator(mode="after")
    def validate_required_database_family(self) -> DatabaseSettings:
        requires_postgresql = self.APP_ENV in _PRODUCTION_ENV_VALUES or self.DB_REQUIRE_POSTGRESQL
        if requires_postgresql and not self.DB_TYPE.startswith("postgresql"):
            raise ValueError("PostgreSQL is required for production-like and Compose deployments.")
        return self
