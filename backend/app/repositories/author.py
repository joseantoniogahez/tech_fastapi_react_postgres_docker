from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import DEFAULT_LIST_LIMIT
from app.common.sorting import AuthorSort
from app.models.author import Author
from app.repositories.base import BaseRepository


class AuthorRepository(BaseRepository[Author]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Author)

    async def list_ordered(
        self,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: AuthorSort = "name",
    ) -> list[Author]:
        return await self.list(offset=offset, limit=limit, sort=sort)

    async def get_by_name(self, name: str) -> Author | None:
        return await self.get_one_by({"name": name})

    async def get_or_create_by_name(self, name: str) -> Author:
        author = await self.get_by_name(name=name)
        if author is not None:
            return author

        try:
            async with self.session.begin_nested():
                return await self.create(name=name)
        except IntegrityError:
            author = await self.get_by_name(name=name)
            if author is not None:
                return author
            raise
