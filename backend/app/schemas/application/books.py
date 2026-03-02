from app.const.book import BookStatus

from .base import ApplicationSchema


class BookMutationCommand(ApplicationSchema):
    title: str
    year: int
    status: BookStatus
    author_id: int | None
    author_name: str
