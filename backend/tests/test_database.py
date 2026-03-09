from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from app.core.config.settings import DatabaseSettings
from app.core.db import database as database_module
from app.core.db.database import (
    DatabaseConfigError,
    DatabaseConnectionType,
    DatabaseManager,
    DatabaseRuntime,
    database_manager,
)


def test_build_network_database_url() -> None:
    settings = DatabaseSettings(
        DB_TYPE="postgresql+asyncpg",
        DB_USER="user",
        DB_PASSWORD="password",  # pragma: allowlist secret
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="app_data",
    )

    url = database_manager.build_network_database_url(settings)

    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "user"
    assert url.password == "password"  # pragma: allowlist secret
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "app_data"


def test_build_file_database_url() -> None:
    settings = DatabaseSettings()

    url = database_manager.build_file_database_url(settings)

    assert url.drivername == "sqlite+aiosqlite"
    assert url.username is None
    assert url.password is None
    assert url.host is None
    assert url.port is None
    assert url.database == "app.db"


def _get_validation_error() -> ValidationError:
    class RequiredFieldModel(BaseModel):
        required: int

    with pytest.raises(ValidationError) as exc_info:
        RequiredFieldModel()  # type: ignore[call-arg]
    return exc_info.value


def test_build_database_url_raises_database_config_error_when_settings_fail() -> None:
    validation_error = _get_validation_error()

    with (
        patch("app.core.db.database.DatabaseSettings", side_effect=validation_error),
        pytest.raises(DatabaseConfigError) as exc_info,
    ):
        database_manager.build_database_url()

    assert "Could not load DB settings from environment variables." in str(exc_info.value)


def test_build_network_database_url_raises_on_missing_required_fields() -> None:
    settings = DatabaseSettings(
        DB_TYPE="postgresql+asyncpg",
        DB_PASSWORD="password",  # pragma: allowlist secret
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="app_data",
    )

    with pytest.raises(DatabaseConfigError) as exc_info:
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
        DB_PASSWORD="password",  # pragma: allowlist secret
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="app_data",
    )
    manager = DatabaseManager(settings_loader=lambda: settings)

    url = manager.build_database_url()

    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "user"
    assert url.password == "password"  # pragma: allowlist secret
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "app_data"


def test_build_database_url_raises_on_unsupported_connection_type() -> None:
    settings = DatabaseSettings()
    manager = DatabaseManager(settings_loader=lambda: settings)

    with pytest.raises(DatabaseConfigError) as exc_info:
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

    with patch("app.core.db.database.create_async_engine", return_value=engine) as create_engine:
        result = DatabaseManager.build_engine(database_url)

    assert result is engine
    create_engine.assert_called_once_with(url=database_url, pool_pre_ping=True)


def test_build_session_factory_builds_engine_and_sessionmaker() -> None:
    database_url = MagicMock()
    engine = MagicMock()
    session_factory = MagicMock()

    with (
        patch.object(DatabaseManager, "build_engine", return_value=engine) as build_engine,
        patch("app.core.db.database.async_sessionmaker", return_value=session_factory) as sessionmaker,
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


def test_module_database_runtime_helpers_delegate_to_runtime() -> None:
    runtime = MagicMock()
    database_url = MagicMock()
    session_factory = MagicMock()
    runtime.get_database_url.return_value = database_url
    runtime.get_session_factory.return_value = session_factory

    with patch.object(database_module, "database_runtime", runtime):
        resolved_database_url = database_module.get_database_url()
        resolved_session_factory = database_module.get_async_session_factory()
        database_module.reset_database_runtime()

    assert resolved_database_url is database_url
    assert resolved_session_factory is session_factory
    runtime.get_database_url.assert_called_once_with(DatabaseConnectionType.AUTO)
    runtime.get_session_factory.assert_called_once_with(DatabaseConnectionType.AUTO)
    runtime.reset.assert_called_once_with()


def test_module_dynamic_attributes_resolve_known_exports_and_include_public_api() -> None:
    database_url = MagicMock()
    session_factory = MagicMock()

    with (
        patch("app.core.db.database.get_database_url", return_value=database_url) as get_database_url,
        patch("app.core.db.database.get_async_session_factory", return_value=session_factory) as get_factory,
    ):
        resolved_database_url = database_module.__getattr__("DATABASE_URL")
        resolved_session_factory = database_module.__getattr__("AsyncSessionDatabase")

    assert resolved_database_url is database_url
    assert resolved_session_factory is session_factory
    get_database_url.assert_called_once_with()
    get_factory.assert_called_once_with()

    names = database_module.__dir__()
    assert "DATABASE_URL" in names
    assert "AsyncSessionDatabase" in names
    assert "reset_database_runtime" in names


def test_module___getattr___raises_for_unknown_attribute() -> None:
    with pytest.raises(AttributeError):
        database_module.__getattr__("UNKNOWN")
