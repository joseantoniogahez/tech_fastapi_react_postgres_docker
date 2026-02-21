from typing import List, Optional

from app.models.author import Author
from app.repositories.author import AuthorRepository
from app.services import Service


class AuthorService(Service):
    def __init__(self, author_repository: AuthorRepository):
        self.author_repository = author_repository

    async def get_all(self) -> List[Author]:
        return await self.author_repository.list_ordered()

    async def get_or_add(self, author_id: Optional[int], name: str) -> Author:
        if author_id is not None:
            author = await self.author_repository.get(author_id)
            if author is not None:
                return author

        return await self.author_repository.get_or_create_by_name(name=name)
