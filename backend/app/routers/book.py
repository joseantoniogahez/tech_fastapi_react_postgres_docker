from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query

from app.const.permission import PermissionId
from app.dependencies import BookServiceDependency, get_authorized_user
from app.models.user import User
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


@router.post("/")
async def add_book(
    book_data: AddBook,
    book_service: BookServiceDependency,
    _authorized_user: Annotated[User, Depends(get_authorized_user(PermissionId.BOOK_CREATE))],
) -> Book:
    book = await book_service.add(book_data)
    return Book.model_validate(book)


@router.put("/{id}")
async def update_book(
    id: int,
    book_data: UpdateBook,
    book_service: BookServiceDependency,
    _authorized_user: Annotated[User, Depends(get_authorized_user(PermissionId.BOOK_UPDATE))],
) -> Optional[Book]:
    book = await book_service.update(id, book_data)
    return Book.model_validate(book) if book else None


@router.delete("/{id}")
async def delete_book(
    id: int,
    book_service: BookServiceDependency,
    _authorized_user: Annotated[User, Depends(get_authorized_user(PermissionId.BOOK_DELETE))],
) -> None:
    await book_service.delete(id)
