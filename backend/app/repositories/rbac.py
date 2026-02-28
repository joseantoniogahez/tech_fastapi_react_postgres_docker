from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import BaseRepository


class RBACRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Role)

    async def list_roles(self) -> list[Role]:
        return await self.list(sort="name")

    async def list_permissions(self) -> list[Permission]:
        result = await self.session.execute(select(Permission).order_by(Permission.id.asc()))
        return list(result.scalars().all())

    async def list_role_permissions(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
    ) -> list[RolePermission]:
        if role_ids == ():
            return []

        query = select(RolePermission)
        if role_ids is not None:
            query = query.where(RolePermission.role_id.in_(role_ids))

        query = query.order_by(RolePermission.role_id.asc(), RolePermission.permission_id.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_role(self, role_id: int) -> Role | None:
        return await self.get(role_id)

    async def role_name_exists(self, name: str, *, exclude_role_id: int | None = None) -> bool:
        query = select(Role.id).where(Role.name == name)
        if exclude_role_id is not None:
            query = query.where(Role.id != exclude_role_id)

        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def create_role(self, *, name: str) -> Role:
        return await self.create(name=name)

    async def update_role(self, role: Role, *, name: str) -> Role:
        return await self.update(role, name=name)

    async def delete_role(self, role_id: int) -> bool:
        role = await self.get(role_id)
        if role is None:
            return False

        await self.session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        await self.session.execute(delete(UserRole).where(UserRole.role_id == role_id))
        await self.session.delete(role)
        await self.session.flush()
        return True

    async def get_permission(self, permission_id: str) -> Permission | None:
        return await self.session.get(Permission, permission_id)

    async def upsert_role_permission(
        self,
        *,
        role_id: int,
        permission_id: str,
        scope: str,
    ) -> RolePermission:
        role_permission = await self.session.get(
            RolePermission,
            {"role_id": role_id, "permission_id": permission_id},
        )
        if role_permission is None:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                scope=scope,
            )
            self.session.add(role_permission)
        else:
            role_permission.scope = scope

        await self.session.flush()
        return role_permission

    async def delete_role_permission(self, *, role_id: int, permission_id: str) -> bool:
        role_permission = await self.session.get(
            RolePermission,
            {"role_id": role_id, "permission_id": permission_id},
        )
        if role_permission is None:
            return False

        await self.session.delete(role_permission)
        await self.session.flush()
        return True

    async def get_user(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def assign_user_role(self, *, user_id: int, role_id: int) -> bool:
        user_role = await self.session.get(
            UserRole,
            {"user_id": user_id, "role_id": role_id},
        )
        if user_role is not None:
            return False

        self.session.add(UserRole(user_id=user_id, role_id=role_id))
        await self.session.flush()
        return True

    async def remove_user_role(self, *, user_id: int, role_id: int) -> bool:
        user_role = await self.session.get(
            UserRole,
            {"user_id": user_id, "role_id": role_id},
        )
        if user_role is None:
            return False

        await self.session.delete(user_role)
        await self.session.flush()
        return True
