from typing import Any, Protocol

from app.const.book import BookStatus
from app.models.book import Book
from app.repositories import DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT
from app.repositories.book import BookSort
from app.schemas.book import AddBook, UpdateBook
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

    async def get(self, entity_id: int) -> Book | None: ...

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

    async def delete(self, entity_id: int) -> bool: ...


class BookServicePort(Protocol):
    async def get_all(
        self,
        author_id: int | None = None,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: BookSort = "id",
    ) -> list[Book]: ...

    async def get_published(self) -> list[Book]: ...

    async def get(self, id: int) -> Book | None: ...

    async def add(self, book_data: AddBook) -> Book: ...

    async def update(self, id: int, book_data: UpdateBook) -> Book | None: ...

    async def delete(self, id: int) -> None: ...


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
    ) -> list[Book]:
        return await self.book_repository.list_catalog(
            author_id=author_id,
            offset=offset,
            limit=limit,
            sort=sort,
        )

    async def get_published(self) -> list[Book]:
        return await self.book_repository.list_published()

    async def get(self, id: int) -> Book | None:
        return await self.book_repository.get(id)

    async def _get_author_id(self, author_id: int | None, author_name: str) -> int:
        author = await self.author_service.get_or_add(author_id=author_id, name=author_name)
        return author.id

    async def add(self, book_data: AddBook) -> Book:
        async with self.unit_of_work:
            author_id = await self._get_author_id(book_data.author_id, book_data.author_name)
            return await self.book_repository.create(
                title=book_data.title,
                year=book_data.year,
                status=book_data.status,
                author_id=author_id,
            )

    async def update(self, id: int, book_data: UpdateBook) -> Book | None:
        async with self.unit_of_work:
            book = await self.book_repository.get(id)
            if book is None:
                return None

            author_id = await self._get_author_id(book_data.author_id, book_data.author_name)
            return await self.book_repository.update(
                book,
                title=book_data.title,
                year=book_data.year,
                status=book_data.status,
                author_id=author_id,
            )

    async def delete(self, id: int) -> None:
        async with self.unit_of_work:
            await self.book_repository.delete(id)
