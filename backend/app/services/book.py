from typing import List, Optional

from sqlalchemy.future import select

from app.models.book import Author, Book
from app.schemas.book import AddBook, UpdateBook
from app.services import Service
from app.services.author import AuthorService


class BookService(Service):
    async def get_all(self) -> List[Book]:
        query = select(Book)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get(self, id) -> Optional[Book]:
        return await self.session.get(Book, id)

    async def _get_author(self, book_data: AddBook) -> Author:
        return await AuthorService(session=self.session).get_or_add(
            id=book_data.author_id, name=book_data.author_name
        )

    async def add(self, book_data: AddBook) -> Book:
        author = await self._get_author(book_data)
        new_book = Book(
            title=book_data.title,
            year=book_data.year,
            status=book_data.status,
            author_id=author.id,
        )
        self.session.add(new_book)
        await self.session.commit()
        await self.session.refresh(new_book)
        return new_book

    async def update(self, book_data: UpdateBook) -> Optional[Book]:
        author = await self._get_author(book_data)
        book = await self.get(book_data.id)
        if book:
            book.title = book_data.title
            book.year = book_data.year
            book.status = book_data.status
            book.author_id = author.id
            await self.session.commit()
            await self.session.refresh(book)
        return book
