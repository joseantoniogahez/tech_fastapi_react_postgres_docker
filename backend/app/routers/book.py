from typing import List, Optional

from fastapi import APIRouter

from app.dependencies import BookServiceDependency
from app.schemas.book import AddBook, Book, UpdateBook

router = APIRouter(
    prefix="/books",
    tags=["books"],
)


@router.get("/")
async def get_books(book_service: BookServiceDependency) -> List[Book]:
    return await book_service.get_all()


@router.post("/")
async def add_book(book_data: AddBook, book_service: BookServiceDependency) -> Book:
    return await book_service.add(book_data)


@router.put("/{id}")
async def update_book(
    book_data: UpdateBook, book_service: BookServiceDependency
) -> Optional[Book]:
    return await book_service.update(book_data)
