import asyncio
from unittest.mock import MagicMock

import pytest

from app.exceptions.repositories import RepositoryException
from app.models.author import Author
from app.repositories.base import BaseRepository
from utils.testing_support.repositories import build_session_mock


def test_get_column_returns_model_column() -> None:
    repository = BaseRepository(session=build_session_mock(), model=Author)

    assert repository._get_column("name") is Author.name


def test_get_column_raises_when_column_is_missing() -> None:
    repository = BaseRepository(session=build_session_mock(), model=Author)

    with pytest.raises(RepositoryException) as exc_info:
        repository._get_column("missing")

    assert "Column 'missing' does not exist on 'Author'" in str(exc_info.value)


def test_build_query_applies_filters_and_sort() -> None:
    repository = BaseRepository(session=build_session_mock(), model=Author)

    query = repository._build_query(filters={"name": "Alice"}, sort="id")
    query_text = str(query)

    assert "FROM authors" in query_text
    assert "WHERE authors.name = :name_1" in query_text
    assert "ORDER BY authors.id" in query_text


def test_build_query_applies_descending_sort_with_stable_tiebreaker() -> None:
    repository = BaseRepository(session=build_session_mock(), model=Author)

    query = repository._build_query(sort="-name")
    query_text = str(query)

    assert "ORDER BY authors.name DESC, authors.id ASC" in query_text


def test_build_query_raises_when_sort_field_is_empty() -> None:
    repository = BaseRepository(session=build_session_mock(), model=Author)

    with pytest.raises(RepositoryException) as exc_info:
        repository._build_query(sort="-")

    assert "Sort field cannot be empty" in str(exc_info.value)


def test_build_creates_entity_instance() -> None:
    repository = BaseRepository(session=build_session_mock(), model=Author)

    entity = repository.build(name="Alice")

    assert isinstance(entity, Author)
    assert entity.name == "Alice"


def test_create_adds_entity_flushes_and_refreshes() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)

    async def run_test() -> None:
        entity = await repository.create(name="Alice")

        assert isinstance(entity, Author)
        assert entity.name == "Alice"
        session.add.assert_called_once_with(entity)
        session.flush.assert_awaited_once()
        session.commit.assert_not_awaited()
        session.refresh.assert_awaited_once_with(entity)

    asyncio.run(run_test())


def test_get_delegates_to_session_get() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    expected = Author(name="Alice")
    session.get.return_value = expected

    async def run_test() -> None:
        result = await repository.get(1)

        assert result is expected
        session.get.assert_awaited_once_with(Author, 1)

    asyncio.run(run_test())


def test_get_one_by_executes_query_and_returns_entity() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    expected = Author(name="Alice")
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute.return_value = result

    async def run_test() -> None:
        entity = await repository.get_one_by({"name": "Alice"})

        assert entity is expected
        session.execute.assert_awaited_once()
        executed_query = session.execute.await_args.args[0]
        assert "WHERE authors.name = :name_1" in str(executed_query)

    asyncio.run(run_test())


def test_list_executes_query_with_pagination_and_returns_entities() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    expected_items = [Author(name="Alice"), Author(name="Bob")]
    scalars = MagicMock()
    scalars.all.return_value = tuple(expected_items)
    result = MagicMock()
    result.scalars.return_value = scalars
    session.execute.return_value = result

    async def run_test() -> None:
        entities = await repository.list(filters={"name": "Alice"}, offset=2, limit=5, sort="id")

        assert entities == expected_items
        session.execute.assert_awaited_once()
        executed_query = session.execute.await_args.args[0]
        query_text = str(executed_query)
        assert "WHERE authors.name = :name_1" in query_text
        assert "ORDER BY authors.id" in query_text
        assert " LIMIT " in query_text
        assert " OFFSET " in query_text

    asyncio.run(run_test())


def test_list_raises_when_offset_is_negative() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)

    async def run_test() -> None:
        with pytest.raises(RepositoryException) as exc_info:
            await repository.list(offset=-1)

        assert "Offset must be greater than or equal to 0" in str(exc_info.value)
        session.execute.assert_not_awaited()

    asyncio.run(run_test())


def test_list_raises_when_limit_is_less_than_one() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)

    async def run_test() -> None:
        with pytest.raises(RepositoryException) as exc_info:
            await repository.list(limit=0)

        assert "Limit must be greater than or equal to 1" in str(exc_info.value)
        session.execute.assert_not_awaited()

    asyncio.run(run_test())


def test_update_merges_and_refreshes_entity() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    entity = Author(name="Alice")
    merged = Author(name="Bob")
    session.merge.return_value = merged

    async def run_test() -> None:
        result = await repository.update(entity, name="Bob")

        assert result is merged
        assert entity.name == "Bob"
        session.merge.assert_awaited_once_with(entity)
        session.flush.assert_awaited_once()
        session.commit.assert_not_awaited()
        session.refresh.assert_awaited_once_with(merged)

    asyncio.run(run_test())


def test_update_raises_when_field_is_invalid() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    entity = Author(name="Alice")

    async def run_test() -> None:
        with pytest.raises(RepositoryException) as exc_info:
            await repository.update(entity, missing="value")

        assert "Column 'missing' does not exist on 'Author'" in str(exc_info.value)

    asyncio.run(run_test())


def test_delete_returns_false_when_entity_does_not_exist() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    session.get.return_value = None

    async def run_test() -> None:
        deleted = await repository.delete(10)

        assert deleted is False
        session.get.assert_awaited_once_with(Author, 10)
        session.delete.assert_not_called()
        session.flush.assert_not_awaited()
        session.commit.assert_not_awaited()

    asyncio.run(run_test())


def test_delete_removes_entity_when_it_exists() -> None:
    session = build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    entity = Author(name="Alice")
    session.get.return_value = entity

    async def run_test() -> None:
        deleted = await repository.delete(20)

        assert deleted is True
        session.get.assert_awaited_once_with(Author, 20)
        session.delete.assert_awaited_once_with(entity)
        session.flush.assert_awaited_once()
        session.commit.assert_not_awaited()

    asyncio.run(run_test())
