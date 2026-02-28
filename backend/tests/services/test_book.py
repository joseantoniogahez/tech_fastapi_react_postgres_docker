import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.common.pagination import DEFAULT_LIST_LIMIT
from app.const.book import BookStatus
from app.models.author import Author
from app.models.book import Book
from app.schemas.book import AddBook, UpdateBook
from app.services.book import BookService


def _build_unit_of_work_mock() -> MagicMock:
    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)
    return unit_of_work


def _build_service() -> tuple[BookService, MagicMock, MagicMock, MagicMock]:
    book_repository = MagicMock()
    book_repository.list_catalog = AsyncMock()
    book_repository.list_published = AsyncMock()
    book_repository.get = AsyncMock()
    book_repository.create = AsyncMock()
    book_repository.update = AsyncMock()
    book_repository.delete = AsyncMock()

    author_service = MagicMock()
    author_service.get_or_add = AsyncMock()
    unit_of_work = _build_unit_of_work_mock()
    service = BookService(
        book_repository=book_repository,
        author_service=author_service,
        unit_of_work=unit_of_work,
    )
    return service, book_repository, author_service, unit_of_work


def test_get_all_delegates_to_list_catalog_with_author_filter() -> None:
    service, book_repository, _, unit_of_work = _build_service()
    expected_books = [
        Book(id=1, title="Dune", year=1965, status=BookStatus.PUBLISHED, author_id=2),
    ]
    book_repository.list_catalog.return_value = expected_books

    async def run_test() -> None:
        books = await service.get_all(author_id=2)

        assert books == expected_books
        book_repository.list_catalog.assert_awaited_once_with(
            author_id=2,
            offset=0,
            limit=DEFAULT_LIST_LIMIT,
            sort="id",
        )
        unit_of_work.__aenter__.assert_not_awaited()
        unit_of_work.__aexit__.assert_not_awaited()

    asyncio.run(run_test())


def test_get_all_delegates_custom_pagination_and_sort() -> None:
    service, book_repository, _, unit_of_work = _build_service()

    async def run_test() -> None:
        await service.get_all(author_id=5, offset=10, limit=7, sort="-year")

        book_repository.list_catalog.assert_awaited_once_with(
            author_id=5,
            offset=10,
            limit=7,
            sort="-year",
        )
        unit_of_work.__aenter__.assert_not_awaited()
        unit_of_work.__aexit__.assert_not_awaited()

    asyncio.run(run_test())


def test_get_published_delegates_to_repository() -> None:
    service, book_repository, _, unit_of_work = _build_service()
    expected_books = [
        Book(id=2, title="Foundation", year=1951, status=BookStatus.PUBLISHED, author_id=3),
    ]
    book_repository.list_published.return_value = expected_books

    async def run_test() -> None:
        books = await service.get_published()

        assert books == expected_books
        book_repository.list_published.assert_awaited_once_with()
        unit_of_work.__aenter__.assert_not_awaited()
        unit_of_work.__aexit__.assert_not_awaited()

    asyncio.run(run_test())


def test_get_delegates_to_repository() -> None:
    service, book_repository, _, unit_of_work = _build_service()
    expected_book = Book(id=3, title="Neuromancer", year=1984, status=BookStatus.DRAFT, author_id=4)
    book_repository.get.return_value = expected_book

    async def run_test() -> None:
        book = await service.get(3)

        assert book is expected_book
        book_repository.get.assert_awaited_once_with(3)
        unit_of_work.__aenter__.assert_not_awaited()
        unit_of_work.__aexit__.assert_not_awaited()

    asyncio.run(run_test())


def test_get_author_id_delegates_to_author_service() -> None:
    service, _, author_service, _ = _build_service()
    author_service.get_or_add.return_value = Author(id=9, name="Ursula Le Guin")

    async def run_test() -> None:
        author_id = await service._get_author_id(author_id=99, author_name="Ursula Le Guin")

        assert author_id == 9
        author_service.get_or_add.assert_awaited_once_with(author_id=99, name="Ursula Le Guin")

    asyncio.run(run_test())


def test_add_creates_book_with_resolved_author_id() -> None:
    service, book_repository, author_service, unit_of_work = _build_service()
    author_service.get_or_add.return_value = Author(id=5, name="Isaac Asimov")
    created_book = Book(id=10, title="I, Robot", year=1950, status=BookStatus.PUBLISHED, author_id=5)
    book_repository.create.return_value = created_book
    book_data = AddBook(
        title="I, Robot",
        year=1950,
        status=BookStatus.PUBLISHED,
        author_id=None,
        author_name="Isaac Asimov",
    )

    async def run_test() -> None:
        result = await service.add(book_data)

        assert result is created_book
        author_service.get_or_add.assert_awaited_once_with(author_id=None, name="Isaac Asimov")
        book_repository.create.assert_awaited_once_with(
            title="I, Robot",
            year=1950,
            status=BookStatus.PUBLISHED,
            author_id=5,
        )
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())


def test_update_returns_none_when_book_does_not_exist() -> None:
    service, book_repository, author_service, unit_of_work = _build_service()
    book_repository.get.return_value = None
    book_data = UpdateBook(
        title="Nonexistent",
        year=2000,
        status=BookStatus.DRAFT,
        author_id=1,
        author_name="Unknown",
    )

    async def run_test() -> None:
        result = await service.update(12, book_data)

        assert result is None
        book_repository.get.assert_awaited_once_with(12)
        author_service.get_or_add.assert_not_awaited()
        book_repository.update.assert_not_awaited()
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())


def test_update_updates_existing_book_with_resolved_author_id() -> None:
    service, book_repository, author_service, unit_of_work = _build_service()
    existing_book = Book(id=20, title="Old Title", year=2001, status=BookStatus.DRAFT, author_id=3)
    updated_book = Book(id=20, title="New Title", year=2002, status=BookStatus.PUBLISHED, author_id=8)
    book_repository.get.return_value = existing_book
    book_repository.update.return_value = updated_book
    author_service.get_or_add.return_value = Author(id=8, name="New Author")
    book_data = UpdateBook(
        title="New Title",
        year=2002,
        status=BookStatus.PUBLISHED,
        author_id=None,
        author_name="New Author",
    )

    async def run_test() -> None:
        result = await service.update(20, book_data)

        assert result is updated_book
        book_repository.get.assert_awaited_once_with(20)
        author_service.get_or_add.assert_awaited_once_with(author_id=None, name="New Author")
        book_repository.update.assert_awaited_once_with(
            existing_book,
            title="New Title",
            year=2002,
            status=BookStatus.PUBLISHED,
            author_id=8,
        )
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())


def test_delete_delegates_to_repository() -> None:
    service, book_repository, _, unit_of_work = _build_service()

    async def run_test() -> None:
        await service.delete(99)
        book_repository.delete.assert_awaited_once_with(99)
        unit_of_work.__aenter__.assert_awaited_once_with()
        unit_of_work.__aexit__.assert_awaited_once_with(None, None, None)

    asyncio.run(run_test())
