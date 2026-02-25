from enum import Enum
from typing import Callable

from pydantic import ValidationError
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.const.settings import DatabaseSettings


class CustomDatabaseException(Exception):
    """Raised when database configuration is invalid."""


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
                raise CustomDatabaseException(f"Missing {field_name} variable")

    def load_settings(self) -> DatabaseSettings:
        loader = self._settings_loader or DatabaseSettings
        try:
            return loader()
        except ValidationError as exc:
            raise CustomDatabaseException("Could not load DB settings from environment variables.") from exc

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

        raise CustomDatabaseException(f"Unsupported DB connection type: {resolved_connection_type}")

    @staticmethod
    def build_engine(database_url: URL) -> AsyncEngine:
        return create_async_engine(url=database_url, pool_pre_ping=True)

    @staticmethod
    def build_session_factory(database_url: URL) -> async_sessionmaker[AsyncSession]:
        engine = database_manager.build_engine(database_url)
        return async_sessionmaker(bind=engine, expire_on_commit=False)


database_manager = DatabaseManager()


DATABASE_URL = database_manager.build_database_url()
AsyncSessionDatabase = database_manager.build_session_factory(DATABASE_URL)
Base = declarative_base()
