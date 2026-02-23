import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.models.author import Author
from app.services.author import AuthorService


def _build_service() -> tuple[AuthorService, MagicMock]:
    author_repository = MagicMock()
    author_repository.list_ordered = AsyncMock()
    author_repository.get = AsyncMock()
    author_repository.get_or_create_by_name = AsyncMock()
    service = AuthorService(author_repository=author_repository)
    return service, author_repository


def test_get_all_delegates_to_list_ordered() -> None:
    service, author_repository = _build_service()
    expected = [Author(id=1, name="Isaac Asimov"), Author(id=2, name="Frank Herbert")]
    author_repository.list_ordered.return_value = expected

    async def run_test() -> None:
        result = await service.get_all()

        assert result == expected
        author_repository.list_ordered.assert_awaited_once_with()

    asyncio.run(run_test())


def test_get_or_add_returns_existing_author_when_id_exists() -> None:
    service, author_repository = _build_service()
    existing_author = Author(id=5, name="Arthur C. Clarke")
    author_repository.get.return_value = existing_author

    async def run_test() -> None:
        result = await service.get_or_add(author_id=5, name="ignored")

        assert result is existing_author
        author_repository.get.assert_awaited_once_with(5)
        author_repository.get_or_create_by_name.assert_not_awaited()

    asyncio.run(run_test())


def test_get_or_add_falls_back_to_name_when_id_not_found() -> None:
    service, author_repository = _build_service()
    created_author = Author(id=6, name="Ursula Le Guin")
    author_repository.get.return_value = None
    author_repository.get_or_create_by_name.return_value = created_author

    async def run_test() -> None:
        result = await service.get_or_add(author_id=99, name="Ursula Le Guin")

        assert result is created_author
        author_repository.get.assert_awaited_once_with(99)
        author_repository.get_or_create_by_name.assert_awaited_once_with(name="Ursula Le Guin")

    asyncio.run(run_test())


def test_get_or_add_uses_name_when_author_id_is_none() -> None:
    service, author_repository = _build_service()
    created_author = Author(id=7, name="Octavia Butler")
    author_repository.get_or_create_by_name.return_value = created_author

    async def run_test() -> None:
        result = await service.get_or_add(author_id=None, name="Octavia Butler")

        assert result is created_author
        author_repository.get.assert_not_awaited()
        author_repository.get_or_create_by_name.assert_awaited_once_with(name="Octavia Butler")

    asyncio.run(run_test())
