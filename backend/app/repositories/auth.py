from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.const.permission import PERMISSION_SCOPE_RANK
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import BaseRepository


class AuthRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        return await self.get_one_by({"username": username})

    async def username_exists(self, username: str, *, exclude_user_id: int | None = None) -> bool:
        query = select(User.id).where(User.username == username)
        if exclude_user_id is not None:
            query = query.where(User.id != exclude_user_id)

        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def get_user_permission_scope(self, user_id: int, permission_id: str) -> str | None:
        query = (
            select(RolePermission.scope)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                RolePermission.permission_id == permission_id,
            )
        )
        result = await self.session.execute(query)
        scopes = tuple(result.scalars().all())
        valid_scopes = [scope for scope in scopes if scope in PERMISSION_SCOPE_RANK]
        if not valid_scopes:
            return None
        return max(valid_scopes, key=lambda scope: PERMISSION_SCOPE_RANK[scope])

    async def user_has_permission(self, user_id: int, permission_id: str) -> bool:
        return await self.get_user_permission_scope(user_id=user_id, permission_id=permission_id) is not None
