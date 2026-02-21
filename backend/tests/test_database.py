from unittest.mock import patch

import pytest
from pydantic import BaseModel, ValidationError

from app.const.settings import DatabaseSettings
from app.database import CustomDatabaseException, _build_postgres_url, build_database_url


def test_build_postgres_url() -> None:
    settings = DatabaseSettings(
        DB_TYPE="postgresql+asyncpg",
        DB_USER="user",
        DB_PASSWORD="password",
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="books",
    )

    url = _build_postgres_url(settings)

    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "user"
    assert url.password == "password"
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "books"


def _get_validation_error() -> ValidationError:
    class RequiredFieldModel(BaseModel):
        required: int

    with pytest.raises(ValidationError) as exc_info:
        RequiredFieldModel()  # type: ignore[call-arg]
    return exc_info.value


def test_build_database_url_raises_custom_exception_when_both_settings_fail() -> None:
    validation_error = _get_validation_error()

    with patch("app.database.DatabaseSettings", side_effect=validation_error), patch(
        "app.database.LocalDatabaseSettings", side_effect=validation_error
    ):
        with pytest.raises(CustomDatabaseException) as exc_info:
            build_database_url()

    assert "Could not load local DB settings from file" in str(exc_info.value)
