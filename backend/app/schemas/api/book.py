from pydantic import ConfigDict, Field

from app.const.book import BookStatus
from app.schemas.api.author import AuthorResponse
from app.schemas.api.base import ApiSchema


class BookBase(ApiSchema):
    title: str = Field(min_length=1, max_length=255)
    year: int
    status: BookStatus

    model_config = ConfigDict(str_strip_whitespace=True)


class CreateBookRequest(BookBase):
    author_id: int | None = None
    author_name: str = Field(min_length=1, max_length=255)


class UpdateBookRequest(CreateBookRequest):
    pass


class BookResponse(BookBase):
    id: int
    author: AuthorResponse

    model_config = ConfigDict(from_attributes=True)
