from typing import List, Optional

from app.models.book import Book
from app.repositories import UnitOfWork
from app.repositories.author import AuthorRepository
from app.repositories.book import BookRepository
from app.schemas.book import AddBook, UpdateBook
from app.services import Service


class BookService(Service):
    def __init__(
        self,
        book_repository: BookRepository,
        author_repository: AuthorRepository,
        unit_of_work: UnitOfWork,
    ):
        self.book_repository = book_repository
        self.author_repository = author_repository
        self.unit_of_work = unit_of_work

    async def get_all(self, author_id: Optional[int] = None) -> List[Book]:
        return await self.book_repository.list_catalog(author_id=author_id)

    async def get_published(self) -> List[Book]:
        return await self.book_repository.list_published()

    async def get(self, id: int) -> Optional[Book]:
        return await self.book_repository.get(id)

    async def _get_author_id(self, author_id: Optional[int], author_name: str) -> int:
        if author_id is not None:
            author = await self.author_repository.get(author_id)
            if author is not None:
                return author.id

        author = await self.author_repository.get_or_create_by_name(name=author_name)
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

    async def update(self, id: int, book_data: UpdateBook) -> Optional[Book]:
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
