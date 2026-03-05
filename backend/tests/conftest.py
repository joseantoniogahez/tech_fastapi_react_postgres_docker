import asyncio
import logging
import pathlib
import tempfile
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from argon2 import PasswordHasher
from starlette.testclient import TestClient

from app.authorization import PERMISSION_SPECS
from app.dependencies.db import get_db_session
from app.infrastructure.database import Base
from app.main import app
from app.models.author import Author
from app.models.book import Book
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_inheritance import RoleInheritance
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from utils.testing_support.database import MockDatabase
from utils.testing_support.fixtures import get_fixture_data, load_mock_data


@pytest.fixture(scope="session", autouse=True)
def set_app_http_logger_to_error() -> None:
    logging.getLogger("app.http").setLevel(logging.ERROR)


@pytest.fixture(scope="module")
def path() -> str:
    return str(pathlib.Path(__file__).parent.resolve())


@pytest.fixture(scope="module")
def mock_authors(path: str) -> list[dict[str, Any]]:
    return get_fixture_data(path, "authors")


@pytest.fixture(scope="module")
def mock_books(path: str) -> list[dict[str, Any]]:
    return get_fixture_data(path, "books")


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
    mock_authors: list[dict[str, Any]],
    mock_books: list[dict[str, Any]],
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
        {"class": Author, "json": mock_authors},
        {"class": Book, "json": mock_books},
    ]


@pytest.fixture(scope="module")
def mock_database(path: str, mock_data: list[dict[str, Any]]) -> Generator[MockDatabase]:
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
