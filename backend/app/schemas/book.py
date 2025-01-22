from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.const.book import BookStatus
from app.schemas.author import Author


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    year: int
    status: BookStatus

    model_config = ConfigDict(str_strip_whitespace=True)


class AddBook(BookBase):
    author_id: Optional[int] = None
    author_name: str = Field(min_length=1, max_length=255)


class UpdateBook(AddBook):
    id: int


class Book(BookBase):
    id: int

    author: Author

    model_config = ConfigDict(from_attributes=True)
