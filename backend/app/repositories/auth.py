from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import BaseRepository


class AuthRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        return await self.get_one_by({"username": username})
