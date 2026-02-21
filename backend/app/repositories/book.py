from sqlalchemy.ext.asyncio import AsyncSession

from app.const.book import BookStatus
from app.models.book import Book
from app.repositories import BaseRepository


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Book)

    async def list_catalog(self, author_id: int | None = None) -> list[Book]:
        filters = {"author_id": author_id} if author_id is not None else None
        return await self.list(filters=filters, order_by="id")

    async def list_published(self) -> list[Book]:
        return await self.list(filters={"status": BookStatus.PUBLISHED}, order_by="id")
