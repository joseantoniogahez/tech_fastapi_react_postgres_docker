import asyncio
import pathlib
from typing import Any, Dict, Generator, List
from unittest.mock import patch

import pytest
from argon2 import PasswordHasher
from starlette.testclient import TestClient

from app.main import app
from app.models import Base
from app.models.author import Author
from app.models.book import Book
from app.models.user import User
from utils.database import MockDatabase
from utils.fixtures import get_fixture_data, load_mock_data


@pytest.fixture(scope="module")
def path() -> str:
    return str(pathlib.Path(__file__).parent.resolve())


@pytest.fixture(scope="module")
def mock_authors(path: str) -> List[Dict[str, Any]]:
    return get_fixture_data(path, "authors")


@pytest.fixture(scope="module")
def mock_books(path: str) -> List[Dict[str, Any]]:
    return get_fixture_data(path, "books")


@pytest.fixture(scope="module")
def mock_users() -> List[Dict[str, Any]]:
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
    ]


@pytest.fixture(scope="module")
def mock_data(
    mock_authors: List[Dict[str, Any]],
    mock_books: List[Dict[str, Any]],
    mock_users: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return [
        {"class": User, "json": mock_users},
        {"class": Author, "json": mock_authors},
        {"class": Book, "json": mock_books},
    ]


@pytest.fixture(scope="module")
def mock_database(path: str, mock_data: List[Dict[str, Any]]) -> Generator[MockDatabase, None, None]:
    mock_db = MockDatabase(db_name="test_db.sql", path=path)
    asyncio.run(mock_db.setup(Base))
    asyncio.run(load_mock_data(mock_data, mock_db))

    yield mock_db

    asyncio.run(mock_db.close())
    del mock_db


@pytest.fixture
def mock_client(
    mock_database: MockDatabase,
) -> Generator[TestClient, None, None]:
    with patch("app.dependencies.AsyncSessionDatabase", mock_database.Session):
        yield TestClient(app)
