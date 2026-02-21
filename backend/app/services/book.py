from typing import List, Optional

from app.models.book import Book
from app.repositories.author import AuthorRepository
from app.repositories.book import BookRepository
from app.schemas.book import AddBook, UpdateBook
from app.services import Service
from app.services.author import AuthorService


class BookService(Service):
    def __init__(self, book_repository: BookRepository, author_repository: AuthorRepository):
        self.book_repository = book_repository
        self.author_service = AuthorService(author_repository=author_repository)

    async def get_all(self, author_id: Optional[int] = None) -> List[Book]:
        return await self.book_repository.list_catalog(author_id=author_id)

    async def get_published(self) -> List[Book]:
        return await self.book_repository.list_published()

    async def get(self, id: int) -> Optional[Book]:
        return await self.book_repository.get(id)

    async def _get_author_id(self, book_data: AddBook) -> int:
        author = await self.author_service.get_or_add(author_id=book_data.author_id, name=book_data.author_name)
        return author.id

    async def add(self, book_data: AddBook) -> Book:
        author_id = await self._get_author_id(book_data)
        return await self.book_repository.create(
            title=book_data.title,
            year=book_data.year,
            status=book_data.status,
            author_id=author_id,
        )

    async def update(self, id: int, book_data: UpdateBook) -> Optional[Book]:
        book = await self.book_repository.get(id)
        if book is None:
            return None

        author_id = await self._get_author_id(book_data)
        return await self.book_repository.update(
            book,
            title=book_data.title,
            year=book_data.year,
            status=book_data.status,
            author_id=author_id,
        )

    async def delete(self, id: int) -> None:
        await self.book_repository.delete(id)
