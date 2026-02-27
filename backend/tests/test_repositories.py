import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from sqlalchemy.exc import IntegrityError

import app.repositories as repositories
from app.exceptions.repositories import RepositoryException
from app.models.author import Author
from app.repositories import BaseRepository, IdType, UnitOfWork
from app.repositories.auth import AuthRepository
from app.repositories.author import AuthorRepository


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


class _AsyncNullTransaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


def test_repositories_module_exports_expected_symbols() -> None:
    assert repositories.BaseRepository is BaseRepository
    assert repositories.UnitOfWork is UnitOfWork
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


def test_build_query_applies_filters_and_sort() -> None:
    repository = BaseRepository(session=_build_session_mock(), model=Author)

    query = repository._build_query(filters={"name": "Alice"}, sort="id")
    query_text = str(query)

    assert "FROM authors" in query_text
    assert "WHERE authors.name = :name_1" in query_text
    assert "ORDER BY authors.id" in query_text


def test_build_query_applies_descending_sort_with_stable_tiebreaker() -> None:
    repository = BaseRepository(session=_build_session_mock(), model=Author)

    query = repository._build_query(sort="-name")
    query_text = str(query)

    assert "ORDER BY authors.name DESC, authors.id ASC" in query_text


def test_build_query_raises_when_sort_field_is_empty() -> None:
    repository = BaseRepository(session=_build_session_mock(), model=Author)

    with pytest.raises(RepositoryException) as exc_info:
        repository._build_query(sort="-")

    assert "Sort field cannot be empty" in str(exc_info.value)


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
    session = _build_session_mock()
    repository = BaseRepository(session=session, model=Author)

    async def run_test() -> None:
        with pytest.raises(RepositoryException) as exc_info:
            await repository.list(offset=-1)

        assert "Offset must be greater than or equal to 0" in str(exc_info.value)
        session.execute.assert_not_awaited()

    asyncio.run(run_test())


def test_list_raises_when_limit_is_less_than_one() -> None:
    session = _build_session_mock()
    repository = BaseRepository(session=session, model=Author)

    async def run_test() -> None:
        with pytest.raises(RepositoryException) as exc_info:
            await repository.list(limit=0)

        assert "Limit must be greater than or equal to 1" in str(exc_info.value)
        session.execute.assert_not_awaited()

    asyncio.run(run_test())


def test_author_get_or_create_by_name_returns_existing_after_integrity_error() -> None:
    session = _build_session_mock()
    session.begin_nested = MagicMock(return_value=_AsyncNullTransaction())
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
    session = _build_session_mock()
    session.begin_nested = MagicMock(return_value=_AsyncNullTransaction())
    repository = AuthorRepository(session=session)
    get_by_name_mock = AsyncMock(side_effect=[None, None])
    create_mock = AsyncMock(side_effect=IntegrityError("insert", {}, Exception("duplicate")))

    async def run_test() -> None:
        with (
            patch.object(repository, "get_by_name", get_by_name_mock),
            patch.object(repository, "create", create_mock),
        ):
            with pytest.raises(IntegrityError):
                await repository.get_or_create_by_name(name="Octavia Butler")

        session.begin_nested.assert_called_once_with()
        create_mock.assert_awaited_once_with(name="Octavia Butler")
        assert get_by_name_mock.await_args_list == [
            call(name="Octavia Butler"),
            call(name="Octavia Butler"),
        ]

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


def test_auth_repository_user_has_permission_delegates_to_scope_lookup() -> None:
    session = _build_session_mock()
    repository = AuthRepository(session=session)

    async def run_test() -> None:
        get_scope_mock = AsyncMock(return_value="any")
        with patch.object(repository, "get_user_permission_scope", get_scope_mock):
            has_permission = await repository.user_has_permission(user_id=3, permission_id="books:update")

        assert has_permission is True
        get_scope_mock.assert_awaited_once_with(
            user_id=3,
            permission_id="books:update",
        )

    asyncio.run(run_test())
