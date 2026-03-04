from fastapi import APIRouter

from app.common.pagination import DEFAULT_LIST_LIMIT
from app.dependencies.authorization import PublicReadAccessDependency
from app.dependencies.authorization_books import BookCreateAuth, BookDeleteAuth, BookUpdateAuth
from app.dependencies.services import BookServiceDependency
from app.exceptions.services import NotFoundError
from app.openapi.books import (
    CREATE_BOOK_DOC,
    DELETE_BOOK_DOC,
    GET_BOOK_DOC,
    GET_BOOKS_DOC,
    GET_PUBLISHED_BOOKS_DOC,
    UPDATE_BOOK_DOC,
    AuthorIdQuery,
    BookIdPath,
    BookSortQuery,
    CreateBookPayload,
    LimitQuery,
    OffsetQuery,
    UpdateBookPayload,
)
from app.schemas.api.book import BookResponse
from app.schemas.application.book import BookMutationCommand

router = APIRouter(
    prefix="/books",
    tags=["books"],
)


@router.get("/", response_model=list[BookResponse], **GET_BOOKS_DOC)
async def get_books(
    book_service: BookServiceDependency,
    _read_access: PublicReadAccessDependency,
    author_id: AuthorIdQuery = None,
    offset: OffsetQuery = 0,
    limit: LimitQuery = DEFAULT_LIST_LIMIT,
    sort: BookSortQuery = "id",
) -> list[BookResponse]:
    books = await book_service.get_all(author_id=author_id, offset=offset, limit=limit, sort=sort)
    return [BookResponse.model_validate(book) for book in books]


@router.get("/published", response_model=list[BookResponse], **GET_PUBLISHED_BOOKS_DOC)
async def get_published_books(
    book_service: BookServiceDependency,
    _read_access: PublicReadAccessDependency,
) -> list[BookResponse]:
    books = await book_service.get_published()
    return [BookResponse.model_validate(book) for book in books]


@router.get("/{book_id}", response_model=BookResponse, **GET_BOOK_DOC)
async def get_book(
    book_service: BookServiceDependency,
    _read_access: PublicReadAccessDependency,
    book_id: BookIdPath,
) -> BookResponse:
    book = await book_service.get(book_id)
    if book is None:
        raise NotFoundError(message=f"Book {book_id} not found", details={"book_id": book_id})
    return BookResponse.model_validate(book)


@router.post("/", response_model=BookResponse, **CREATE_BOOK_DOC)
async def create_book(
    book_service: BookServiceDependency,
    _authorized_user: BookCreateAuth,
    book_data: CreateBookPayload,
) -> BookResponse:
    book = await book_service.create(BookMutationCommand.from_api(book_data))
    return BookResponse.model_validate(book)


@router.put("/{book_id}", response_model=BookResponse, **UPDATE_BOOK_DOC)
async def update_book(
    book_service: BookServiceDependency,
    _authorized_user: BookUpdateAuth,
    book_id: BookIdPath,
    book_data: UpdateBookPayload,
) -> BookResponse:
    book = await book_service.update(book_id, BookMutationCommand.from_api(book_data))
    if book is None:
        raise NotFoundError(message=f"Book {book_id} not found", details={"book_id": book_id})
    return BookResponse.model_validate(book)


@router.delete("/{book_id}", **DELETE_BOOK_DOC)
async def delete_book(
    book_service: BookServiceDependency,
    _authorized_user: BookDeleteAuth,
    book_id: BookIdPath,
) -> None:
    await book_service.delete(book_id)
