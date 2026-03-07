from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.records import (
    PermissionRecord,
    RoleInheritanceRecord,
    RolePermissionRecord,
    RoleRecord,
    UserRecord,
)
from app.core.db.repository_base import BaseRepository
from app.core.errors.repositories import RepositoryConflictError, RepositoryError
from app.features.auth.models import User
from app.features.rbac.models import Permission, Role, RoleInheritance, RolePermission, UserRole


class RBACRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Role, default_record_type=RoleRecord)

    async def list_roles(self) -> list[RoleRecord]:
        roles = await self.list(sort="name")
        return self._to_records(roles)

    async def list_permissions(self) -> list[PermissionRecord]:
        result = await self.session.execute(select(Permission).order_by(Permission.id.asc()))
        permissions = list(result.scalars().all())
        return self._to_records(permissions, PermissionRecord)

    async def list_role_permissions(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
    ) -> list[RolePermissionRecord]:
        if role_ids == ():
            return []

        query = select(RolePermission)
        if role_ids is not None:
            query = query.where(RolePermission.role_id.in_(role_ids))

        query = query.order_by(RolePermission.role_id.asc(), RolePermission.permission_id.asc())
        result = await self.session.execute(query)
        role_permissions = list(result.scalars().all())
        return self._to_records(role_permissions, RolePermissionRecord)

    async def list_role_inheritances(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
    ) -> list[RoleInheritanceRecord]:
        if role_ids == ():
            return []

        query = select(RoleInheritance)
        if role_ids is not None:
            query = query.where(RoleInheritance.role_id.in_(role_ids))

        query = query.order_by(RoleInheritance.role_id.asc(), RoleInheritance.parent_role_id.asc())
        result = await self.session.execute(query)
        role_inheritances = list(result.scalars().all())
        return self._to_records(role_inheritances, RoleInheritanceRecord)

    async def get_role(self, role_id: int) -> RoleRecord | None:
        role = await super().get(role_id)
        if role is None:
            return None
        return self._to_record(role)

    async def role_name_exists(self, name: str, *, exclude_role_id: int | None = None) -> bool:
        query = select(Role.id).where(Role.name == name)
        if exclude_role_id is not None:
            query = query.where(Role.id != exclude_role_id)

        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def create_role(self, *, name: str) -> RoleRecord:
        try:
            role = await self.create(name=name)
            return self._to_record(role)
        except IntegrityError as exc:
            raise RepositoryConflictError(
                message="Role name already exists",
                details={"name": name},
            ) from exc

    async def update_role(self, role_id: int, *, name: str) -> RoleRecord:
        role = await super().get(role_id)
        if role is None:
            raise RepositoryError(f"Role {role_id} not found")

        try:
            updated_role = await self.update(role, name=name)
            return self._to_record(updated_role)
        except IntegrityError as exc:
            raise RepositoryConflictError(
                message="Role name already exists",
                details={"name": name},
            ) from exc

    async def delete_role(self, role_id: int) -> bool:
        role = await self.get(role_id)
        if role is None:
            return False

        await self.session.execute(
            delete(RoleInheritance).where(
                or_(
                    RoleInheritance.role_id == role_id,
                    RoleInheritance.parent_role_id == role_id,
                )
            )
        )
        await self.session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        await self.session.execute(delete(UserRole).where(UserRole.role_id == role_id))
        await self.session.delete(role)
        await self.session.flush()
        return True

    async def get_permission(self, permission_id: str) -> PermissionRecord | None:
        permission = await self.session.get(Permission, permission_id)
        if permission is None:
            return None
        return self._to_record(permission, PermissionRecord)

    async def upsert_role_permission(
        self,
        *,
        role_id: int,
        permission_id: str,
        scope: str,
    ) -> RolePermissionRecord:
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
        return self._to_record(role_permission, RolePermissionRecord)

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

    async def get_user(self, user_id: int) -> UserRecord | None:
        user = await self.session.get(User, user_id)
        if user is None:
            return None
        return self._to_record(user, UserRecord)

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

    async def assign_role_inheritance(self, *, role_id: int, parent_role_id: int) -> bool:
        role_inheritance = await self.session.get(
            RoleInheritance,
            {"role_id": role_id, "parent_role_id": parent_role_id},
        )
        if role_inheritance is not None:
            return False

        self.session.add(RoleInheritance(role_id=role_id, parent_role_id=parent_role_id))
        await self.session.flush()
        return True

    async def remove_role_inheritance(self, *, role_id: int, parent_role_id: int) -> bool:
        role_inheritance = await self.session.get(
            RoleInheritance,
            {"role_id": role_id, "parent_role_id": parent_role_id},
        )
        if role_inheritance is None:
            return False

        await self.session.delete(role_inheritance)
        await self.session.flush()
        return True
