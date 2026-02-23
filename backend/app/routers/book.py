from typing import List, Optional

from fastapi import APIRouter

from app.dependencies import BookServiceDependency
from app.dependencies.authorization import (
    BookCreateAuthorizedUserDependency,
    BookDeleteAuthorizedUserDependency,
    BookUpdateAuthorizedUserDependency,
)
from app.exceptions import NotFoundException
from app.openapi.books import (
    ADD_BOOK_DOC,
    DELETE_BOOK_DOC,
    GET_BOOK_DOC,
    GET_BOOKS_DOC,
    GET_PUBLISHED_BOOKS_DOC,
    UPDATE_BOOK_DOC,
    AddBookPayload,
    AuthorIdQuery,
    BookIdPath,
    UpdateBookPayload,
)
from app.schemas.book import Book

router = APIRouter(
    prefix="/books",
    tags=["books"],
)


@router.get("/", response_model=List[Book], **GET_BOOKS_DOC)
async def get_books(
    book_service: BookServiceDependency,
    author_id: AuthorIdQuery = None,
) -> List[Book]:
    books = await book_service.get_all(author_id)
    return [Book.model_validate(book) for book in books]


@router.get("/published", response_model=List[Book], **GET_PUBLISHED_BOOKS_DOC)
async def get_published_books(book_service: BookServiceDependency) -> List[Book]:
    books = await book_service.get_published()
    return [Book.model_validate(book) for book in books]


@router.get("/{id}", response_model=Book, **GET_BOOK_DOC)
async def get_book(
    book_service: BookServiceDependency,
    id: BookIdPath,
) -> Book:
    book = await book_service.get(id)
    if book is None:
        raise NotFoundException(message=f"Book {id} not found", details={"id": id})
    return Book.model_validate(book)


@router.post("/", response_model=Book, **ADD_BOOK_DOC)
async def add_book(
    book_service: BookServiceDependency,
    _authorized_user: BookCreateAuthorizedUserDependency,
    book_data: AddBookPayload,
) -> Book:
    book = await book_service.add(book_data)
    return Book.model_validate(book)


@router.put("/{id}", response_model=Optional[Book], **UPDATE_BOOK_DOC)
async def update_book(
    book_service: BookServiceDependency,
    _authorized_user: BookUpdateAuthorizedUserDependency,
    id: BookIdPath,
    book_data: UpdateBookPayload,
) -> Optional[Book]:
    book = await book_service.update(id, book_data)
    return Book.model_validate(book) if book else None


@router.delete("/{id}", **DELETE_BOOK_DOC)
async def delete_book(
    book_service: BookServiceDependency,
    _authorized_user: BookDeleteAuthorizedUserDependency,
    id: BookIdPath,
) -> None:
    await book_service.delete(id)
