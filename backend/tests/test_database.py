from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from app.const.settings import DatabaseSettings
from app.infrastructure import database as database_module
from app.infrastructure.database import (
    CustomDatabaseException,
    DatabaseConnectionType,
    DatabaseManager,
    DatabaseRuntime,
    database_manager,
)


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

    with patch("app.infrastructure.database.DatabaseSettings", side_effect=validation_error):
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


def test_database_runtime_loads_database_url_lazily_and_caches_it() -> None:
    settings = DatabaseSettings()
    settings_loader = MagicMock(return_value=settings)
    manager = DatabaseManager(settings_loader=settings_loader)
    runtime = DatabaseRuntime(manager)

    assert settings_loader.call_count == 0

    first_url = runtime.get_database_url()
    second_url = runtime.get_database_url()

    assert first_url is second_url
    settings_loader.assert_called_once_with()


def test_database_runtime_reset_clears_cached_session_factory() -> None:
    manager = MagicMock(spec=DatabaseManager)
    database_url = MagicMock()
    first_session_factory = MagicMock()
    second_session_factory = MagicMock()
    manager.build_database_url.return_value = database_url
    manager.build_session_factory.side_effect = [first_session_factory, second_session_factory]
    runtime = DatabaseRuntime(manager)

    assert runtime.get_session_factory() is first_session_factory
    assert runtime.get_session_factory() is first_session_factory

    runtime.reset()

    assert runtime.get_session_factory() is second_session_factory
    assert manager.build_database_url.call_count == 2
    assert manager.build_session_factory.call_count == 2


def test_build_engine_creates_async_engine_with_pool_pre_ping() -> None:
    database_url = MagicMock()
    engine = MagicMock()

    with patch("app.infrastructure.database.create_async_engine", return_value=engine) as create_engine:
        result = DatabaseManager.build_engine(database_url)

    assert result is engine
    create_engine.assert_called_once_with(url=database_url, pool_pre_ping=True)


def test_build_session_factory_builds_engine_and_sessionmaker() -> None:
    database_url = MagicMock()
    engine = MagicMock()
    session_factory = MagicMock()

    with (
        patch.object(DatabaseManager, "build_engine", return_value=engine) as build_engine,
        patch("app.infrastructure.database.async_sessionmaker", return_value=session_factory) as sessionmaker,
    ):
        result = DatabaseManager.build_session_factory(database_url)

    assert result is session_factory
    build_engine.assert_called_once_with(database_url)
    sessionmaker.assert_called_once_with(bind=engine, expire_on_commit=False)


def test_database_runtime_builds_database_url_for_explicit_connection_type() -> None:
    manager = MagicMock(spec=DatabaseManager)
    explicit_url = MagicMock()
    manager.build_database_url.return_value = explicit_url
    runtime = DatabaseRuntime(manager)

    result = runtime.get_database_url(DatabaseConnectionType.FILE)

    assert result is explicit_url
    manager.build_database_url.assert_called_once_with(DatabaseConnectionType.FILE)


def test_database_runtime_builds_session_factory_for_explicit_connection_type() -> None:
    manager = MagicMock(spec=DatabaseManager)
    explicit_url = MagicMock()
    session_factory = MagicMock()
    manager.build_database_url.return_value = explicit_url
    manager.build_session_factory.return_value = session_factory
    runtime = DatabaseRuntime(manager)

    result = runtime.get_session_factory(DatabaseConnectionType.NETWORK)

    assert result is session_factory
    manager.build_database_url.assert_called_once_with(DatabaseConnectionType.NETWORK)
    manager.build_session_factory.assert_called_once_with(explicit_url)


def test_module_get_database_url_delegates_to_runtime() -> None:
    runtime = MagicMock()
    database_url = MagicMock()
    runtime.get_database_url.return_value = database_url

    with patch.object(database_module, "database_runtime", runtime):
        result = database_module.get_database_url()

    assert result is database_url
    runtime.get_database_url.assert_called_once_with(DatabaseConnectionType.AUTO)


def test_module_get_async_session_factory_delegates_to_runtime() -> None:
    runtime = MagicMock()
    session_factory = MagicMock()
    runtime.get_session_factory.return_value = session_factory

    with patch.object(database_module, "database_runtime", runtime):
        result = database_module.get_async_session_factory()

    assert result is session_factory
    runtime.get_session_factory.assert_called_once_with(DatabaseConnectionType.AUTO)


def test_module_reset_database_runtime_delegates_to_runtime() -> None:
    runtime = MagicMock()

    with patch.object(database_module, "database_runtime", runtime):
        database_module.reset_database_runtime()

    runtime.reset.assert_called_once_with()


def test_module___getattr___resolves_database_url() -> None:
    database_url = MagicMock()

    with patch("app.infrastructure.database.get_database_url", return_value=database_url) as get_database_url:
        result = database_module.__getattr__("DATABASE_URL")

    assert result is database_url
    get_database_url.assert_called_once_with()


def test_module___getattr___resolves_async_session_database() -> None:
    session_factory = MagicMock()

    with patch("app.infrastructure.database.get_async_session_factory", return_value=session_factory) as get_factory:
        result = database_module.__getattr__("AsyncSessionDatabase")

    assert result is session_factory
    get_factory.assert_called_once_with()


def test_module___getattr___raises_for_unknown_attribute() -> None:
    with pytest.raises(AttributeError):
        database_module.__getattr__("UNKNOWN")


def test_module___dir___includes_public_database_api() -> None:
    names = database_module.__dir__()

    assert "DATABASE_URL" in names
    assert "AsyncSessionDatabase" in names
    assert "reset_database_runtime" in names
