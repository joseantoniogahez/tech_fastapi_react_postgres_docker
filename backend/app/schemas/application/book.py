from pydantic import ConfigDict

from app.const.book import BookStatus

from .author import AuthorResult
from .base import ApplicationSchema


class BookMutationCommand(ApplicationSchema):
    title: str
    year: int
    status: BookStatus
    author_id: int | None
    author_name: str


class BookResult(ApplicationSchema):
    id: int
    title: str
    year: int
    status: BookStatus
    author: AuthorResult

    model_config = ConfigDict(frozen=True, from_attributes=True)
