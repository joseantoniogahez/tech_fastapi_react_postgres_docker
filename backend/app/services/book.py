from typing import Any, Protocol

from app.common.pagination import DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT
from app.common.sorting import BookSort
from app.const.book import BookStatus
from app.models.book import Book
from app.schemas.application.book import BookMutationCommand, BookResult
from app.services import UnitOfWorkPort
from app.services.author import AuthorServicePort


class BookRepositoryPort(Protocol):
    async def list_catalog(
        self,
        author_id: int | None = None,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: BookSort = "id",
    ) -> list[Book]: ...

    async def list_published(self, *, offset: int = 0, limit: int = MAX_LIST_LIMIT) -> list[Book]: ...

    async def get(self, book_id: int) -> Book | None: ...

    async def create(
        self,
        *,
        title: str,
        year: int,
        status: BookStatus,
        author_id: int,
    ) -> Book: ...

    async def update(
        self,
        entity: Book,
        **changes: Any,
    ) -> Book: ...

    async def delete(self, book_id: int) -> bool: ...


class BookServicePort(Protocol):
    async def get_all(
        self,
        author_id: int | None = None,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: BookSort = "id",
    ) -> list[BookResult]: ...

    async def get_published(self) -> list[BookResult]: ...

    async def get(self, book_id: int) -> BookResult | None: ...

    async def create(self, book_data: BookMutationCommand) -> BookResult: ...

    async def update(self, book_id: int, book_data: BookMutationCommand) -> BookResult | None: ...

    async def delete(self, book_id: int) -> None: ...


class BookService:
    def __init__(
        self,
        book_repository: BookRepositoryPort,
        author_service: AuthorServicePort,
        unit_of_work: UnitOfWorkPort,
    ):
        self.book_repository = book_repository
        self.author_service = author_service
        self.unit_of_work = unit_of_work

    async def get_all(
        self,
        author_id: int | None = None,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: BookSort = "id",
    ) -> list[BookResult]:
        books = await self.book_repository.list_catalog(
            author_id=author_id,
            offset=offset,
            limit=limit,
            sort=sort,
        )
        return BookResult.from_domain_list(books)

    async def get_published(self) -> list[BookResult]:
        books = await self.book_repository.list_published()
        return BookResult.from_domain_list(books)

    async def get(self, book_id: int) -> BookResult | None:
        book = await self.book_repository.get(book_id)
        if book is None:
            return None
        return BookResult.from_domain(book)

    async def _resolve_author_id(self, author_id: int | None, author_name: str) -> int:
        author = await self.author_service.get_by_id_or_create_by_name(author_id=author_id, name=author_name)
        return author.id

    async def create(self, book_data: BookMutationCommand) -> BookResult:
        async with self.unit_of_work:
            author_id = await self._resolve_author_id(book_data.author_id, book_data.author_name)
            book = await self.book_repository.create(
                title=book_data.title,
                year=book_data.year,
                status=book_data.status,
                author_id=author_id,
            )
        return BookResult.from_domain(book)

    async def update(self, book_id: int, book_data: BookMutationCommand) -> BookResult | None:
        async with self.unit_of_work:
            book = await self.book_repository.get(book_id)
            if book is None:
                return None

            author_id = await self._resolve_author_id(book_data.author_id, book_data.author_name)
            updated_book = await self.book_repository.update(
                book,
                title=book_data.title,
                year=book_data.year,
                status=book_data.status,
                author_id=author_id,
            )
        return BookResult.from_domain(updated_book)

    async def delete(self, book_id: int) -> None:
        async with self.unit_of_work:
            await self.book_repository.delete(book_id)
