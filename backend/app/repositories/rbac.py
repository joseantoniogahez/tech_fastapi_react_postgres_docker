from collections.abc import Iterable

from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.authorization import PERMISSION_SCOPE_RANK
from app.exceptions.repositories import RepositoryConflictError
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_inheritance import RoleInheritance
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.base import BaseRepository


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

    async def list_role_inheritances(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
    ) -> list[RoleInheritance]:
        if role_ids == ():
            return []

        query = select(RoleInheritance)
        if role_ids is not None:
            query = query.where(RoleInheritance.role_id.in_(role_ids))

        query = query.order_by(RoleInheritance.role_id.asc(), RoleInheritance.parent_role_id.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    def _merge_scope(current_scope: str | None, candidate_scope: str) -> str:
        if current_scope is None:
            return candidate_scope
        if PERMISSION_SCOPE_RANK.get(candidate_scope, -1) > PERMISSION_SCOPE_RANK.get(current_scope, -1):
            return candidate_scope
        return current_scope

    @staticmethod
    def _build_direct_permission_map(role_permissions: Iterable[RolePermission]) -> dict[int, dict[str, str]]:
        direct_permissions: dict[int, dict[str, str]] = {}
        for role_permission in role_permissions:
            if role_permission.scope not in PERMISSION_SCOPE_RANK:
                continue

            role_permissions_map = direct_permissions.setdefault(role_permission.role_id, {})
            existing_scope = role_permissions_map.get(role_permission.permission_id)
            role_permissions_map[role_permission.permission_id] = RBACRepository._merge_scope(
                existing_scope,
                role_permission.scope,
            )
        return direct_permissions

    @staticmethod
    def _build_parents_map(role_inheritances: Iterable[RoleInheritance]) -> dict[int, tuple[int, ...]]:
        parents_by_role_id: dict[int, tuple[int, ...]] = {}
        for role_inheritance in role_inheritances:
            current_parents = parents_by_role_id.get(role_inheritance.role_id, ())
            parents_by_role_id[role_inheritance.role_id] = current_parents + (role_inheritance.parent_role_id,)
        return parents_by_role_id

    @staticmethod
    def _resolve_target_role_ids(
        *,
        role_ids: tuple[int, ...] | None,
        direct_permissions_by_role_id: dict[int, dict[str, str]],
        parents_by_role_id: dict[int, tuple[int, ...]],
    ) -> list[int]:
        if role_ids is None:
            return sorted(set(direct_permissions_by_role_id) | set(parents_by_role_id))
        return sorted(set(role_ids))

    def _resolve_effective_permissions_for_role(
        self,
        *,
        role_id: int,
        parents_by_role_id: dict[int, tuple[int, ...]],
        direct_permissions_by_role_id: dict[int, dict[str, str]],
        memoized_effective_permissions: dict[int, dict[str, str]],
        resolving_role_ids: set[int],
    ) -> dict[str, str]:
        cached = memoized_effective_permissions.get(role_id)
        if cached is not None:
            return cached
        if role_id in resolving_role_ids:
            return {}

        resolving_role_ids.add(role_id)
        effective_permissions = dict(direct_permissions_by_role_id.get(role_id, {}))
        for parent_role_id in parents_by_role_id.get(role_id, ()):
            parent_permissions = self._resolve_effective_permissions_for_role(
                role_id=parent_role_id,
                parents_by_role_id=parents_by_role_id,
                direct_permissions_by_role_id=direct_permissions_by_role_id,
                memoized_effective_permissions=memoized_effective_permissions,
                resolving_role_ids=resolving_role_ids,
            )
            for permission_id, parent_scope in parent_permissions.items():
                existing_scope = effective_permissions.get(permission_id)
                effective_permissions[permission_id] = self._merge_scope(existing_scope, parent_scope)

        resolving_role_ids.remove(role_id)
        memoized_effective_permissions[role_id] = effective_permissions
        return effective_permissions

    def _build_effective_role_permission_rows(
        self,
        *,
        target_role_ids: list[int],
        parents_by_role_id: dict[int, tuple[int, ...]],
        direct_permissions_by_role_id: dict[int, dict[str, str]],
    ) -> list[RolePermission]:
        memoized_effective_permissions: dict[int, dict[str, str]] = {}
        resolving_role_ids: set[int] = set()
        effective_role_permissions: list[RolePermission] = []
        for role_id in target_role_ids:
            effective_permissions = self._resolve_effective_permissions_for_role(
                role_id=role_id,
                parents_by_role_id=parents_by_role_id,
                direct_permissions_by_role_id=direct_permissions_by_role_id,
                memoized_effective_permissions=memoized_effective_permissions,
                resolving_role_ids=resolving_role_ids,
            )
            for permission_id in sorted(effective_permissions):
                effective_role_permissions.append(
                    RolePermission(
                        role_id=role_id,
                        permission_id=permission_id,
                        scope=effective_permissions[permission_id],
                    )
                )
        return effective_role_permissions

    async def list_effective_role_permissions(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
    ) -> list[RolePermission]:
        if role_ids == ():
            return []

        direct_role_permissions = await self.list_role_permissions()
        role_inheritances = await self.list_role_inheritances()
        parents_by_role_id = self._build_parents_map(role_inheritances)
        direct_permissions_by_role_id = self._build_direct_permission_map(direct_role_permissions)
        target_role_ids = self._resolve_target_role_ids(
            role_ids=role_ids,
            direct_permissions_by_role_id=direct_permissions_by_role_id,
            parents_by_role_id=parents_by_role_id,
        )
        return self._build_effective_role_permission_rows(
            target_role_ids=target_role_ids,
            parents_by_role_id=parents_by_role_id,
            direct_permissions_by_role_id=direct_permissions_by_role_id,
        )

    async def get_role(self, role_id: int) -> Role | None:
        return await self.get(role_id)

    async def role_name_exists(self, name: str, *, exclude_role_id: int | None = None) -> bool:
        query = select(Role.id).where(Role.name == name)
        if exclude_role_id is not None:
            query = query.where(Role.id != exclude_role_id)

        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def create_role(self, *, name: str) -> Role:
        try:
            return await self.create(name=name)
        except IntegrityError as exc:
            raise RepositoryConflictError(
                message="Role name already exists",
                details={"name": name},
            ) from exc

    async def update_role(self, role: Role, *, name: str) -> Role:
        try:
            return await self.update(role, name=name)
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
