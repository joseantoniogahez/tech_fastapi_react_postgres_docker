from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from threading import RLock

from pydantic import ValidationError
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.const.settings import DatabaseSettings


class DatabaseConfigError(Exception):
    pass


class DatabaseConnectionType(str, Enum):
    AUTO = "auto"
    NETWORK = "network"
    FILE = "file"


class DatabaseManager:
    _NETWORK_REQUIRED_FIELDS = (
        "DB_TYPE",
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
    )
    _FILE_REQUIRED_FIELDS = ("DB_TYPE", "DB_NAME")

    def __init__(self, settings_loader: Callable[[], DatabaseSettings] | None = None) -> None:
        self._settings_loader = settings_loader

    @staticmethod
    def _is_missing(value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        return False

    def _validate_required_fields(
        self,
        db_settings: DatabaseSettings,
        field_names: tuple[str, ...],
    ) -> None:
        for field_name in field_names:
            if self._is_missing(getattr(db_settings, field_name)):
                raise DatabaseConfigError(f"Missing {field_name} variable")

    def load_settings(self) -> DatabaseSettings:
        loader = self._settings_loader or DatabaseSettings
        try:
            return loader()
        except ValidationError as exc:
            raise DatabaseConfigError("Could not load DB settings from environment variables.") from exc

    def resolve_connection_type(
        self,
        db_settings: DatabaseSettings,
        requested_type: DatabaseConnectionType,
    ) -> DatabaseConnectionType:
        if requested_type != DatabaseConnectionType.AUTO:
            return requested_type
        return (
            DatabaseConnectionType.FILE if db_settings.DB_TYPE.startswith("sqlite") else DatabaseConnectionType.NETWORK
        )

    def build_network_database_url(self, db_settings: DatabaseSettings) -> URL:
        self._validate_required_fields(db_settings, self._NETWORK_REQUIRED_FIELDS)
        return URL.create(
            drivername=db_settings.DB_TYPE,
            username=db_settings.DB_USER,
            password=db_settings.DB_PASSWORD,
            host=db_settings.DB_HOST,
            port=db_settings.DB_PORT,
            database=db_settings.DB_NAME,
        )

    def build_file_database_url(self, db_settings: DatabaseSettings) -> URL:
        self._validate_required_fields(db_settings, self._FILE_REQUIRED_FIELDS)
        return URL.create(drivername=db_settings.DB_TYPE, database=db_settings.DB_NAME)

    def build_database_url(
        self,
        db_connection_type: DatabaseConnectionType = DatabaseConnectionType.AUTO,
    ) -> URL:
        db_settings = self.load_settings()
        resolved_connection_type = self.resolve_connection_type(
            db_settings,
            db_connection_type,
        )

        if resolved_connection_type == DatabaseConnectionType.NETWORK:
            return self.build_network_database_url(db_settings)
        if resolved_connection_type == DatabaseConnectionType.FILE:
            return self.build_file_database_url(db_settings)

        raise DatabaseConfigError(f"Unsupported DB connection type: {resolved_connection_type}")

    @staticmethod
    def build_engine(database_url: URL) -> AsyncEngine:
        return create_async_engine(url=database_url, pool_pre_ping=True)

    @staticmethod
    def build_session_factory(database_url: URL) -> async_sessionmaker[AsyncSession]:
        engine = DatabaseManager.build_engine(database_url)
        return async_sessionmaker(bind=engine, expire_on_commit=False)


class DatabaseRuntime:
    def __init__(self, manager: DatabaseManager) -> None:
        self._manager = manager
        self._database_url: URL | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._lock = RLock()

    def get_database_url(
        self,
        db_connection_type: DatabaseConnectionType = DatabaseConnectionType.AUTO,
    ) -> URL:
        if db_connection_type != DatabaseConnectionType.AUTO:
            return self._manager.build_database_url(db_connection_type)

        if self._database_url is not None:
            return self._database_url

        with self._lock:
            if self._database_url is None:
                self._database_url = self._manager.build_database_url()
            return self._database_url

    def get_session_factory(
        self,
        db_connection_type: DatabaseConnectionType = DatabaseConnectionType.AUTO,
    ) -> async_sessionmaker[AsyncSession]:
        if db_connection_type != DatabaseConnectionType.AUTO:
            database_url = self._manager.build_database_url(db_connection_type)
            return self._manager.build_session_factory(database_url)

        if self._session_factory is not None:
            return self._session_factory

        with self._lock:
            if self._session_factory is None:
                self._session_factory = self._manager.build_session_factory(self.get_database_url())
            return self._session_factory

    def reset(self) -> None:
        with self._lock:
            self._database_url = None
            self._session_factory = None


Base = declarative_base()
database_manager = DatabaseManager()
database_runtime = DatabaseRuntime(database_manager)


def get_database_url(
    db_connection_type: DatabaseConnectionType = DatabaseConnectionType.AUTO,
) -> URL:
    return database_runtime.get_database_url(db_connection_type)


def get_async_session_factory(
    db_connection_type: DatabaseConnectionType = DatabaseConnectionType.AUTO,
) -> async_sessionmaker[AsyncSession]:
    return database_runtime.get_session_factory(db_connection_type)


def reset_database_runtime() -> None:
    database_runtime.reset()


def __getattr__(name: str) -> object:
    if name == "DATABASE_URL":
        return get_database_url()
    if name == "AsyncSessionDatabase":
        return get_async_session_factory()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(
        {
            "AsyncSessionDatabase",
            "Base",
            "DatabaseConfigError",
            "DATABASE_URL",
            "DatabaseConnectionType",
            "DatabaseManager",
            "DatabaseRuntime",
            "DatabaseSettings",
            "database_manager",
            "database_runtime",
            "get_async_session_factory",
            "get_database_url",
            "reset_database_runtime",
        }
    )
