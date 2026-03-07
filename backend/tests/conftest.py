import asyncio
import logging
import tempfile
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from argon2 import PasswordHasher
from starlette.testclient import TestClient

from app.core.authorization import PERMISSION_SPECS
from app.core.db.database import Base
from app.core.setup.dependencies import get_db_session
from app.features.auth.models import User
from app.features.outbox.models import OutboxEvent
from app.features.rbac.models import Permission, Role, RoleInheritance, RolePermission, UserRole
from app.main import app
from utils.testing_support.database import MockDatabase
from utils.testing_support.fixtures import load_mock_data


@pytest.fixture(scope="session", autouse=True)
def set_app_http_logger_to_error() -> None:
    logging.getLogger("app.http").setLevel(logging.ERROR)


@pytest.fixture(scope="module")
def mock_users() -> list[dict[str, Any]]:
    password_hasher = PasswordHasher()
    return [
        {
            "id": 1,
            "username": "admin",
            "hashed_password": password_hasher.hash("admin123"),
            "disabled": False,
        },
        {
            "id": 2,
            "username": "disabled_user",
            "hashed_password": password_hasher.hash("admin123"),
            "disabled": True,
        },
        {
            "id": 3,
            "username": "reader_user",
            "hashed_password": password_hasher.hash("reader123"),
            "disabled": False,
        },
    ]


@pytest.fixture(scope="module")
def mock_roles() -> list[dict[str, Any]]:
    return [
        {"id": 1, "name": "admin_role"},
        {"id": 2, "name": "reader_role"},
    ]


@pytest.fixture(scope="module")
def mock_permissions() -> list[dict[str, Any]]:
    return [{"id": permission_id, "name": permission_name} for permission_id, permission_name in PERMISSION_SPECS]


@pytest.fixture(scope="module")
def mock_user_roles() -> list[dict[str, Any]]:
    return [
        {"user_id": 1, "role_id": 1},
        {"user_id": 3, "role_id": 2},
    ]


@pytest.fixture(scope="module")
def mock_role_permissions() -> list[dict[str, Any]]:
    return [{"role_id": 1, "permission_id": permission_id} for permission_id, _ in PERMISSION_SPECS]


@pytest.fixture(scope="module")
def mock_data(
    mock_users: list[dict[str, Any]],
    mock_roles: list[dict[str, Any]],
    mock_permissions: list[dict[str, Any]],
    mock_user_roles: list[dict[str, Any]],
    mock_role_permissions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {"class": User, "json": mock_users},
        {"class": Role, "json": mock_roles},
        {"class": Permission, "json": mock_permissions},
        {"class": UserRole, "json": mock_user_roles},
        {"class": RolePermission, "json": mock_role_permissions},
        {"class": RoleInheritance, "json": []},
        {"class": OutboxEvent, "json": []},
    ]


@pytest.fixture(scope="module")
def mock_database(mock_data: list[dict[str, Any]]) -> Generator[MockDatabase]:
    with tempfile.TemporaryDirectory(prefix="backend-tests-db-") as db_tmp_dir:
        mock_db = MockDatabase(path=db_tmp_dir, echo=False)
        asyncio.run(mock_db.setup(Base))
        asyncio.run(load_mock_data(mock_data, mock_db))

        yield mock_db

        asyncio.run(mock_db.close())


@pytest.fixture
def mock_client(
    mock_database: MockDatabase,
) -> Generator[TestClient]:
    async def override_db_session() -> AsyncGenerator[Any]:
        async with mock_database.Session() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
