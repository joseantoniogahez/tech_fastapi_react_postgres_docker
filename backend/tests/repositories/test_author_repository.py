import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.author import Author
from app.repositories.author import AuthorRepository
from utils.testing_support.repositories import AsyncNullTransaction, build_session_mock


def test_author_get_or_create_by_name_returns_existing_after_integrity_error() -> None:
    session = build_session_mock()
    session.begin_nested = MagicMock(return_value=AsyncNullTransaction())
    repository = AuthorRepository(session=session)
    existing_author = Author(id=8, name="Octavia Butler")
    get_by_name_mock = AsyncMock(side_effect=[None, existing_author])
    create_mock = AsyncMock(side_effect=IntegrityError("insert", {}, Exception("duplicate")))

    async def run_test() -> None:
        with (
            patch.object(repository, "get_by_name", get_by_name_mock),
            patch.object(repository, "create", create_mock),
        ):
            entity = await repository.get_or_create_by_name(name="Octavia Butler")

        assert entity is existing_author
        session.begin_nested.assert_called_once_with()
        create_mock.assert_awaited_once_with(name="Octavia Butler")
        assert get_by_name_mock.await_args_list == [
            call(name="Octavia Butler"),
            call(name="Octavia Butler"),
        ]

    asyncio.run(run_test())


def test_author_get_or_create_by_name_reraises_integrity_error_when_author_stays_missing() -> None:
    session = build_session_mock()
    session.begin_nested = MagicMock(return_value=AsyncNullTransaction())
    repository = AuthorRepository(session=session)
    get_by_name_mock = AsyncMock(side_effect=[None, None])
    create_mock = AsyncMock(side_effect=IntegrityError("insert", {}, Exception("duplicate")))

    async def run_test() -> None:
        with (
            patch.object(repository, "get_by_name", get_by_name_mock),
            patch.object(repository, "create", create_mock),
            pytest.raises(IntegrityError),
        ):
            await repository.get_or_create_by_name(name="Octavia Butler")

        session.begin_nested.assert_called_once_with()
        create_mock.assert_awaited_once_with(name="Octavia Butler")
        assert get_by_name_mock.await_args_list == [
            call(name="Octavia Butler"),
            call(name="Octavia Butler"),
        ]

    asyncio.run(run_test())
