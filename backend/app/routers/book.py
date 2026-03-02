from typing import List

from fastapi import APIRouter

from app.common.pagination import DEFAULT_LIST_LIMIT
from app.dependencies.authorization import PublicReadAccessDependency
from app.dependencies.authorization_books import BookCreateAuth, BookDeleteAuth, BookUpdateAuth
from app.dependencies.services import BookServiceDependency
from app.exceptions.services import NotFoundException
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
    BookSortQuery,
    LimitQuery,
    OffsetQuery,
    UpdateBookPayload,
)
from app.schemas.api.book import Book
from app.schemas.application.books import BookMutationCommand

router = APIRouter(
    prefix="/books",
    tags=["books"],
)


@router.get("/", response_model=List[Book], **GET_BOOKS_DOC)
async def get_books(
    book_service: BookServiceDependency,
    _read_access: PublicReadAccessDependency,
    author_id: AuthorIdQuery = None,
    offset: OffsetQuery = 0,
    limit: LimitQuery = DEFAULT_LIST_LIMIT,
    sort: BookSortQuery = "id",
) -> List[Book]:
    books = await book_service.get_all(author_id=author_id, offset=offset, limit=limit, sort=sort)
    return [Book.model_validate(book) for book in books]


@router.get("/published", response_model=List[Book], **GET_PUBLISHED_BOOKS_DOC)
async def get_published_books(
    book_service: BookServiceDependency,
    _read_access: PublicReadAccessDependency,
) -> List[Book]:
    books = await book_service.get_published()
    return [Book.model_validate(book) for book in books]


@router.get("/{id}", response_model=Book, **GET_BOOK_DOC)
async def get_book(
    book_service: BookServiceDependency,
    _read_access: PublicReadAccessDependency,
    id: BookIdPath,
) -> Book:
    book = await book_service.get(id)
    if book is None:
        raise NotFoundException(message=f"Book {id} not found", details={"id": id})
    return Book.model_validate(book)


@router.post("/", response_model=Book, **ADD_BOOK_DOC)
async def add_book(
    book_service: BookServiceDependency,
    _authorized_user: BookCreateAuth,
    book_data: AddBookPayload,
) -> Book:
    book = await book_service.add(BookMutationCommand.from_api(book_data))
    return Book.model_validate(book)


@router.put("/{id}", response_model=Book, **UPDATE_BOOK_DOC)
async def update_book(
    book_service: BookServiceDependency,
    _authorized_user: BookUpdateAuth,
    id: BookIdPath,
    book_data: UpdateBookPayload,
) -> Book:
    book = await book_service.update(id, BookMutationCommand.from_api(book_data))
    if book is None:
        raise NotFoundException(message=f"Book {id} not found", details={"id": id})
    return Book.model_validate(book)


@router.delete("/{id}", **DELETE_BOOK_DOC)
async def delete_book(
    book_service: BookServiceDependency,
    _authorized_user: BookDeleteAuth,
    id: BookIdPath,
) -> None:
    await book_service.delete(id)
