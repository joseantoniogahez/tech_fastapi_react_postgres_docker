from typing import List, Optional

from fastapi import APIRouter, Query

from app.dependencies import BookServiceDependency
from app.dependencies.authorization import (
    BookCreateAuthorizedUserDependency,
    BookDeleteAuthorizedUserDependency,
    BookUpdateAuthorizedUserDependency,
)
from app.exceptions import NotFoundException
from app.schemas.book import AddBook, Book, UpdateBook

router = APIRouter(
    prefix="/books",
    tags=["books"],
)


@router.get("/")
async def get_books(
    book_service: BookServiceDependency,
    author_id: Optional[int] = Query(None, description="Filter books by author ID"),
) -> List[Book]:
    books = await book_service.get_all(author_id)
    return [Book.model_validate(book) for book in books]


@router.get("/published")
async def get_published_books(book_service: BookServiceDependency) -> List[Book]:
    books = await book_service.get_published()
    return [Book.model_validate(book) for book in books]


@router.get("/{id}")
async def get_book(id: int, book_service: BookServiceDependency) -> Book:
    book = await book_service.get(id)
    if book is None:
        raise NotFoundException(message=f"Book {id} not found", details={"id": id})
    return Book.model_validate(book)


@router.post("/")
async def add_book(
    book_data: AddBook,
    book_service: BookServiceDependency,
    _authorized_user: BookCreateAuthorizedUserDependency,
) -> Book:
    book = await book_service.add(book_data)
    return Book.model_validate(book)


@router.put("/{id}")
async def update_book(
    id: int,
    book_data: UpdateBook,
    book_service: BookServiceDependency,
    _authorized_user: BookUpdateAuthorizedUserDependency,
) -> Optional[Book]:
    book = await book_service.update(id, book_data)
    return Book.model_validate(book) if book else None


@router.delete("/{id}")
async def delete_book(
    id: int,
    book_service: BookServiceDependency,
    _authorized_user: BookDeleteAuthorizedUserDependency,
) -> None:
    await book_service.delete(id)
