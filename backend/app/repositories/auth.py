import hashlib
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.authorization import PERMISSION_SCOPE_RANK
from app.exceptions.repositories import RepositoryConflictError, RepositoryInternalError
from app.models.role_inheritance import RoleInheritance
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.base import BaseRepository


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

    async def create(self, **kwargs: Any) -> User:
        try:
            return await super().create(**kwargs)
        except IntegrityError as exc:
            username = kwargs.get("username")
            if isinstance(username, str):
                raise RepositoryConflictError(
                    message="Username already exists",
                    details={"username": username},
                ) from exc
            raise RepositoryInternalError() from exc

    async def update(self, entity: User, **changes: Any) -> User:
        try:
            return await super().update(entity, **changes)
        except IntegrityError as exc:
            username = changes.get("username")
            if isinstance(username, str):
                raise RepositoryConflictError(
                    message="Username already exists",
                    details={"username": username},
                ) from exc
            raise RepositoryInternalError() from exc

    @staticmethod
    def _build_effective_roles_cte(user_id: int):
        effective_roles = (
            select(UserRole.role_id.label("role_id"))
            .where(UserRole.user_id == user_id)
            .cte(name="effective_roles", recursive=True)
        )
        parent_roles = select(RoleInheritance.parent_role_id.label("role_id")).join(
            effective_roles,
            RoleInheritance.role_id == effective_roles.c.role_id,
        )
        return effective_roles.union(parent_roles)

    async def get_rbac_version(self, user_id: int) -> str:
        effective_roles = self._build_effective_roles_cte(user_id)
        query = select(RolePermission.permission_id, RolePermission.scope).join(
            effective_roles, RolePermission.role_id == effective_roles.c.role_id
        )
        result = await self.session.execute(query)

        effective_scopes: dict[str, str] = {}
        for permission_id, scope in result.all():
            if scope not in PERMISSION_SCOPE_RANK:
                continue

            current_scope = effective_scopes.get(permission_id)
            if current_scope is None or PERMISSION_SCOPE_RANK[scope] > PERMISSION_SCOPE_RANK[current_scope]:
                effective_scopes[permission_id] = scope

        serialized_scopes = "|".join(
            f"{permission_id}:{effective_scopes[permission_id]}" for permission_id in sorted(effective_scopes)
        )
        return hashlib.sha256(serialized_scopes.encode("utf-8")).hexdigest()

    async def get_user_permission_scope(self, user_id: int, permission_id: str) -> str | None:
        effective_roles = self._build_effective_roles_cte(user_id)
        query = (
            select(RolePermission.scope)
            .join(effective_roles, RolePermission.role_id == effective_roles.c.role_id)
            .where(
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
