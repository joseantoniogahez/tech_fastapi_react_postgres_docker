import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

import app.repositories as repositories
from app.models.author import Author
from app.repositories import BaseRepository, IdType, RepositoryException, UnitOfWork


def _build_session_mock() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.merge = AsyncMock()
    session.delete = AsyncMock()
    return session


def test_repositories_module_exports_expected_symbols() -> None:
    assert repositories.__all__ == ["BaseRepository", "UnitOfWork", "RepositoryException", "IdType"]
    assert repositories.BaseRepository is BaseRepository
    assert repositories.UnitOfWork is UnitOfWork
    assert repositories.RepositoryException is RepositoryException
    assert repositories.IdType is IdType
    assert IdType is int


def test_get_column_returns_model_column() -> None:
    repository = BaseRepository(session=_build_session_mock(), model=Author)

    assert repository._get_column("name") is Author.name


def test_get_column_raises_when_column_is_missing() -> None:
    repository = BaseRepository(session=_build_session_mock(), model=Author)

    with pytest.raises(RepositoryException) as exc_info:
        repository._get_column("missing")

    assert "Column 'missing' does not exist on 'Author'" in str(exc_info.value)


def test_build_query_applies_filters_and_order_by() -> None:
    repository = BaseRepository(session=_build_session_mock(), model=Author)

    query = repository._build_query(filters={"name": "Alice"}, order_by="id")
    query_text = str(query)

    assert "FROM authors" in query_text
    assert "WHERE authors.name = :name_1" in query_text
    assert "ORDER BY authors.id" in query_text


def test_build_creates_entity_instance() -> None:
    repository = BaseRepository(session=_build_session_mock(), model=Author)

    entity = repository.build(name="Alice")

    assert isinstance(entity, Author)
    assert entity.name == "Alice"


def test_create_adds_entity_flushes_and_refreshes() -> None:
    session = _build_session_mock()
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
    session = _build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    expected = Author(name="Alice")
    session.get.return_value = expected

    async def run_test() -> None:
        result = await repository.get(1)

        assert result is expected
        session.get.assert_awaited_once_with(Author, 1)

    asyncio.run(run_test())


def test_get_one_by_executes_query_and_returns_entity() -> None:
    session = _build_session_mock()
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
    session = _build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    expected_items = [Author(name="Alice"), Author(name="Bob")]
    scalars = MagicMock()
    scalars.all.return_value = tuple(expected_items)
    result = MagicMock()
    result.scalars.return_value = scalars
    session.execute.return_value = result

    async def run_test() -> None:
        entities = await repository.list(filters={"name": "Alice"}, offset=2, limit=5, order_by="id")

        assert entities == expected_items
        session.execute.assert_awaited_once()
        executed_query = session.execute.await_args.args[0]
        query_text = str(executed_query)
        assert "WHERE authors.name = :name_1" in query_text
        assert "ORDER BY authors.id" in query_text
        assert " LIMIT " in query_text
        assert " OFFSET " in query_text

    asyncio.run(run_test())


def test_update_merges_and_refreshes_entity() -> None:
    session = _build_session_mock()
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
    session = _build_session_mock()
    repository = BaseRepository(session=session, model=Author)
    entity = Author(name="Alice")

    async def run_test() -> None:
        with pytest.raises(RepositoryException) as exc_info:
            await repository.update(entity, missing="value")

        assert "Column 'missing' does not exist on 'Author'" in str(exc_info.value)

    asyncio.run(run_test())


def test_delete_returns_false_when_entity_does_not_exist() -> None:
    session = _build_session_mock()
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
    session = _build_session_mock()
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


def test_unit_of_work_commits_when_scope_succeeds() -> None:
    session = _build_session_mock()
    unit_of_work = UnitOfWork(session=session)

    async def run_test() -> None:
        async with unit_of_work:
            pass

        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()

    asyncio.run(run_test())


def test_unit_of_work_rolls_back_when_scope_fails() -> None:
    session = _build_session_mock()
    unit_of_work = UnitOfWork(session=session)

    async def run_test() -> None:
        with pytest.raises(RuntimeError):
            async with unit_of_work:
                raise RuntimeError("boom")

        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()

    asyncio.run(run_test())


def test_unit_of_work_commits_once_for_nested_successful_scopes() -> None:
    session = _build_session_mock()
    unit_of_work = UnitOfWork(session=session)

    async def run_test() -> None:
        async with unit_of_work:
            async with unit_of_work:
                pass

        session.commit.assert_awaited_once()
        session.rollback.assert_not_awaited()

    asyncio.run(run_test())


def test_unit_of_work_skips_commit_after_inner_scope_failure_even_if_handled() -> None:
    session = _build_session_mock()
    unit_of_work = UnitOfWork(session=session)

    async def run_test() -> None:
        async with unit_of_work:
            try:
                async with unit_of_work:
                    raise ValueError("inner failure")
            except ValueError:
                pass

        session.rollback.assert_awaited_once()
        session.commit.assert_not_awaited()

    asyncio.run(run_test())
