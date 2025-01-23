from typing import List

from sqlalchemy.future import select

from app.models.book import Author
from app.services import Service


class AuthorService(Service):
    async def get_all(self) -> List[Author]:
        query = select(Author)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_or_add(self, id, name):
        author = None
        if id:
            author = await self.session.get(Author, id)
        if not author:
            author = Author(name=name)
            self.session.add(author)
            await self.session.flush()
        return author
