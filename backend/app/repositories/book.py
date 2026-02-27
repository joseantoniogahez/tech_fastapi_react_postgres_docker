from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.const.book import BookStatus
from app.models.book import Book
from app.repositories import DEFAULT_LIST_LIMIT, MAX_LIST_LIMIT, BaseRepository

BookSort = Literal["id", "-id", "title", "-title", "year", "-year"]


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)

    async def list_catalog(
        self,
        author_id: int | None = None,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: BookSort = "id",
    ) -> list[Book]:
        filters = {"author_id": author_id} if author_id is not None else None
        return await self.list(filters=filters, offset=offset, limit=limit, sort=sort)

    async def list_published(self, *, offset: int = 0, limit: int = MAX_LIST_LIMIT) -> list[Book]:
        return await self.list(filters={"status": BookStatus.PUBLISHED}, offset=offset, limit=limit, sort="id")
