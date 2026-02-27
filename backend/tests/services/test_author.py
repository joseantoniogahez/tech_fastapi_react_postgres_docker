import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.models.author import Author
from app.repositories import DEFAULT_LIST_LIMIT
from app.services.author import AuthorService


def _build_unit_of_work_mock() -> MagicMock:
    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)
    return unit_of_work


def _build_service() -> tuple[AuthorService, MagicMock, MagicMock]:
    author_repository = MagicMock()
    author_repository.list_ordered = AsyncMock()
    author_repository.get = AsyncMock()
    author_repository.get_or_create_by_name = AsyncMock()
    unit_of_work = _build_unit_of_work_mock()
    service = AuthorService(author_repository=author_repository, unit_of_work=unit_of_work)
    return service, author_repository, unit_of_work


def test_get_all_delegates_to_list_ordered() -> None:
    service, author_repository, unit_of_work = _build_service()
    expected = [Author(id=1, name="Isaac Asimov"), Author(id=2, name="Frank Herbert")]
    author_repository.list_ordered.return_value = expected

    async def run_test() -> None:
        result = await service.get_all()

        assert result == expected
        author_repository.list_ordered.assert_awaited_once_with(offset=0, limit=DEFAULT_LIST_LIMIT, sort="name")
        unit_of_work.__aenter__.assert_not_awaited()
        unit_of_work.__aexit__.assert_not_awaited()

    asyncio.run(run_test())


def test_get_all_delegates_custom_pagination_and_sort() -> None:
    service, author_repository, unit_of_work = _build_service()

    async def run_test() -> None:
        await service.get_all(offset=3, limit=2, sort="-name")

        author_repository.list_ordered.assert_awaited_once_with(offset=3, limit=2, sort="-name")
        unit_of_work.__aenter__.assert_not_awaited()
        unit_of_work.__aexit__.assert_not_awaited()

    asyncio.run(run_test())


def test_get_or_add_returns_existing_author_when_id_exists() -> None:
    service, author_repository, unit_of_work = _build_service()
    existing_author = Author(id=5, name="Arthur C. Clarke")
    author_repository.get.return_value = existing_author

    async def run_test() -> None:
        result = await service.get_or_add(author_id=5, name="ignored")

        assert result is existing_author
        author_repository.get.assert_awaited_once_with(5)
        author_repository.get_or_create_by_name.assert_not_awaited()
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())


def test_get_or_add_falls_back_to_name_when_id_not_found() -> None:
    service, author_repository, unit_of_work = _build_service()
    created_author = Author(id=6, name="Ursula Le Guin")
    author_repository.get.return_value = None
    author_repository.get_or_create_by_name.return_value = created_author

    async def run_test() -> None:
        result = await service.get_or_add(author_id=99, name="Ursula Le Guin")

        assert result is created_author
        author_repository.get.assert_awaited_once_with(99)
        author_repository.get_or_create_by_name.assert_awaited_once_with(name="Ursula Le Guin")
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())


def test_get_or_add_uses_name_when_author_id_is_none() -> None:
    service, author_repository, unit_of_work = _build_service()
    created_author = Author(id=7, name="Octavia Butler")
    author_repository.get_or_create_by_name.return_value = created_author

    async def run_test() -> None:
        result = await service.get_or_add(author_id=None, name="Octavia Butler")

        assert result is created_author
        author_repository.get.assert_not_awaited()
        author_repository.get_or_create_by_name.assert_awaited_once_with(name="Octavia Butler")
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())
