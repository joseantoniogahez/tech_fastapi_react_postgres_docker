from unittest.mock import patch

import pytest
from pydantic import BaseModel, ValidationError

from app.const.settings import DatabaseSettings
from app.database import CustomDatabaseException, DatabaseConnectionType, DatabaseManager, database_manager


def test_build_network_database_url() -> None:
    settings = DatabaseSettings(
        DB_TYPE="postgresql+asyncpg",
        DB_USER="user",
        DB_PASSWORD="password",
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="books",
    )

    url = database_manager.build_network_database_url(settings)

    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "user"
    assert url.password == "password"
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "books"


def test_build_file_database_url() -> None:
    settings = DatabaseSettings()

    url = database_manager.build_file_database_url(settings)

    assert url.drivername == "sqlite+aiosqlite"
    assert url.username is None
    assert url.password is None
    assert url.host is None
    assert url.port is None
    assert url.database == "library.db"


def _get_validation_error() -> ValidationError:
    class RequiredFieldModel(BaseModel):
        required: int

    with pytest.raises(ValidationError) as exc_info:
        RequiredFieldModel()  # type: ignore[call-arg]
    return exc_info.value


def test_build_database_url_raises_custom_exception_when_settings_fail() -> None:
    validation_error = _get_validation_error()

    with patch("app.database.DatabaseSettings", side_effect=validation_error):
        with pytest.raises(CustomDatabaseException) as exc_info:
            database_manager.build_database_url()

    assert "Could not load DB settings from environment variables." in str(exc_info.value)


def test_build_network_database_url_raises_on_missing_required_fields() -> None:
    settings = DatabaseSettings(
        DB_TYPE="postgresql+asyncpg",
        DB_PASSWORD="password",
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="books",
    )

    with pytest.raises(CustomDatabaseException) as exc_info:
        database_manager.build_network_database_url(settings)

    assert "Missing DB_USER variable" in str(exc_info.value)


def test_resolve_connection_type_returns_explicit_requested_type() -> None:
    settings = DatabaseSettings()
    manager = DatabaseManager()

    resolved = manager.resolve_connection_type(settings, DatabaseConnectionType.FILE)

    assert resolved == DatabaseConnectionType.FILE


def test_build_database_url_returns_network_url_for_network_settings() -> None:
    settings = DatabaseSettings(
        DB_TYPE="postgresql+asyncpg",
        DB_USER="user",
        DB_PASSWORD="password",
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="books",
    )
    manager = DatabaseManager(settings_loader=lambda: settings)

    url = manager.build_database_url()

    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "user"
    assert url.password == "password"
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "books"


def test_build_database_url_raises_on_unsupported_connection_type() -> None:
    settings = DatabaseSettings()
    manager = DatabaseManager(settings_loader=lambda: settings)

    with pytest.raises(CustomDatabaseException) as exc_info:
        manager.build_database_url("unsupported")  # type: ignore[arg-type]

    assert "Unsupported DB connection type: unsupported" in str(exc_info.value)
