from typing import Protocol

from app.models.author import Author
from app.repositories import DEFAULT_LIST_LIMIT
from app.repositories.author import AuthorSort
from app.services import UnitOfWorkPort


class AuthorRepositoryPort(Protocol):
    async def list_ordered(
        self,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: AuthorSort = "id",
    ) -> list[Author]: ...

    async def get(self, entity_id: int) -> Author | None: ...

    async def get_or_create_by_name(self, name: str) -> Author: ...


class AuthorServicePort(Protocol):
    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: AuthorSort = "id",
    ) -> list[Author]: ...

    async def get_or_add(self, author_id: int | None, name: str) -> Author: ...


class AuthorService:
    def __init__(self, author_repository: AuthorRepositoryPort, unit_of_work: UnitOfWorkPort):
        self.author_repository = author_repository
        self.unit_of_work = unit_of_work

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = DEFAULT_LIST_LIMIT,
        sort: AuthorSort = "id",
    ) -> list[Author]:
        return await self.author_repository.list_ordered(offset=offset, limit=limit, sort=sort)

    async def get_or_add(self, author_id: int | None, name: str) -> Author:
        async with self.unit_of_work:
            if author_id is not None:
                author = await self.author_repository.get(author_id)
                if author is not None:
                    return author

            return await self.author_repository.get_or_create_by_name(name=name)
