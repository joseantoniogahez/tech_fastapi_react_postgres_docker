from typing import List, Optional

from fastapi import APIRouter, Query

from app.dependencies import BookServiceDependency
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
    return await book_service.get_all(author_id)


@router.post("/")
async def add_book(book_data: AddBook, book_service: BookServiceDependency) -> Book:
    return await book_service.add(book_data)


@router.put("/{id}")
async def update_book(
    id: int, book_data: UpdateBook, book_service: BookServiceDependency
) -> Optional[Book]:
    return await book_service.update(id, book_data)


@router.delete("/{id}")
async def delete_book(id: int, book_service: BookServiceDependency) -> None:
    await book_service.delete(id)
