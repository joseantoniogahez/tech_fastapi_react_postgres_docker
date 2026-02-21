from sqlalchemy.ext.asyncio import AsyncSession

from app.models.author import Author
from app.repositories import BaseRepository


class AuthorRepository(BaseRepository[Author]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Author)

    async def list_ordered(self) -> list[Author]:
        return await self.list(order_by="id")

    async def get_by_name(self, name: str) -> Author | None:
        return await self.get_one_by({"name": name})

    async def get_or_create_by_name(self, name: str) -> Author:
        author = await self.get_by_name(name=name)
        if author is not None:
            return author
        return await self.create(name=name)
