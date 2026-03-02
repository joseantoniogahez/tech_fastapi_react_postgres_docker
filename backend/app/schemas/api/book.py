from typing import Optional

from pydantic import ConfigDict, Field

from app.const.book import BookStatus
from app.schemas.api.author import Author
from app.schemas.api.base import ApiSchema


class BookBase(ApiSchema):
    title: str = Field(min_length=1, max_length=255)
    year: int
    status: BookStatus

    model_config = ConfigDict(str_strip_whitespace=True)


class AddBook(BookBase):
    author_id: Optional[int] = None
    author_name: str = Field(min_length=1, max_length=255)


class UpdateBook(AddBook):
    pass


class Book(BookBase):
    id: int
    author: Author

    model_config = ConfigDict(from_attributes=True)
