from typing import Protocol

from app.const.permission import normalize_permission_scope
from app.exceptions.services import ConflictException, InvalidInputException, NotFoundException
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.schemas.rbac import (
    CreateRole,
    RBACPermission,
    RBACRole,
    RBACRolePermission,
    SetRolePermission,
    UpdateRole,
    UserRoleAssignment,
)
from app.services import UnitOfWorkPort


class RBACRepositoryPort(Protocol):
    async def list_roles(self) -> list[Role]: ...

    async def list_permissions(self) -> list[Permission]: ...

    async def list_role_permissions(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
    ) -> list[RolePermission]: ...

    async def get_role(self, role_id: int) -> Role | None: ...

    async def role_name_exists(self, name: str, *, exclude_role_id: int | None = None) -> bool: ...

    async def create_role(self, *, name: str) -> Role: ...

    async def update_role(self, role: Role, *, name: str) -> Role: ...

    async def delete_role(self, role_id: int) -> bool: ...

    async def get_permission(self, permission_id: str) -> Permission | None: ...

    async def upsert_role_permission(
        self,
        *,
        role_id: int,
        permission_id: str,
        scope: str,
    ) -> RolePermission: ...

    async def delete_role_permission(self, *, role_id: int, permission_id: str) -> bool: ...

    async def get_user(self, user_id: int) -> User | None: ...

    async def assign_user_role(self, *, user_id: int, role_id: int) -> bool: ...

    async def remove_user_role(self, *, user_id: int, role_id: int) -> bool: ...


class RBACServicePort(Protocol):
    async def list_roles(self) -> list[RBACRole]: ...

    async def list_permissions(self) -> list[RBACPermission]: ...

    async def create_role(self, role_data: CreateRole) -> RBACRole: ...

    async def update_role(self, role_id: int, role_data: UpdateRole) -> RBACRole: ...

    async def delete_role(self, role_id: int) -> None: ...

    async def assign_role_permission(
        self,
        role_id: int,
        permission_id: str,
        assignment: SetRolePermission,
    ) -> RBACRolePermission: ...

    async def remove_role_permission(self, role_id: int, permission_id: str) -> None: ...

    async def assign_user_role(self, user_id: int, role_id: int) -> UserRoleAssignment: ...

    async def remove_user_role(self, user_id: int, role_id: int) -> None: ...


class RBACService:
    def __init__(
        self,
        rbac_repository: RBACRepositoryPort,
        unit_of_work: UnitOfWorkPort,
    ):
        self.rbac_repository = rbac_repository
        self.unit_of_work = unit_of_work

    @staticmethod
    def _normalize_role_name(name: str) -> str:
        normalized_name = name.strip().lower()
        if not normalized_name:
            raise InvalidInputException(message="Role name is required")
        return normalized_name

    @staticmethod
    def _build_permission_name_map(permissions: list[Permission]) -> dict[str, str]:
        return {permission.id: permission.name for permission in permissions}

    @staticmethod
    def _group_role_permissions(
        role_permissions: list[RolePermission],
    ) -> dict[int, list[RolePermission]]:
        permissions_by_role_id: dict[int, list[RolePermission]] = {}
        for role_permission in role_permissions:
            permissions_by_role_id.setdefault(role_permission.role_id, []).append(role_permission)
        return permissions_by_role_id

    @staticmethod
    def _build_role_permission_schema(
        role_permission: RolePermission,
        permission_names: dict[str, str],
    ) -> RBACRolePermission:
        return RBACRolePermission(
            id=role_permission.permission_id,
            name=permission_names.get(role_permission.permission_id, role_permission.permission_id),
            scope=role_permission.scope,
        )

    def _build_role_schema(
        self,
        role: Role,
        role_permissions: list[RolePermission],
        permission_names: dict[str, str],
    ) -> RBACRole:
        return RBACRole(
            id=role.id,
            name=role.name,
            permissions=[
                self._build_role_permission_schema(role_permission, permission_names)
                for role_permission in role_permissions
            ],
        )

    async def _get_role_or_raise(self, role_id: int) -> Role:
        role = await self.rbac_repository.get_role(role_id)
        if role is None:
            raise NotFoundException(message=f"Role {role_id} not found", details={"id": role_id})
        return role

    async def _get_permission_or_raise(self, permission_id: str) -> Permission:
        permission = await self.rbac_repository.get_permission(permission_id)
        if permission is None:
            raise NotFoundException(
                message=f"Permission {permission_id} not found",
                details={"permission_id": permission_id},
            )
        return permission

    async def _get_user_or_raise(self, user_id: int) -> User:
        user = await self.rbac_repository.get_user(user_id)
        if user is None:
            raise NotFoundException(message=f"User {user_id} not found", details={"id": user_id})
        return user

    async def _build_role_response(self, role: Role) -> RBACRole:
        permissions = await self.rbac_repository.list_permissions()
        permission_names = self._build_permission_name_map(permissions)
        role_permissions = await self.rbac_repository.list_role_permissions(role_ids=(role.id,))
        return self._build_role_schema(role, role_permissions, permission_names)

    async def list_roles(self) -> list[RBACRole]:
        roles = await self.rbac_repository.list_roles()
        if not roles:
            return []

        permissions = await self.rbac_repository.list_permissions()
        permission_names = self._build_permission_name_map(permissions)
        role_permissions = await self.rbac_repository.list_role_permissions(role_ids=tuple(role.id for role in roles))
        permissions_by_role_id = self._group_role_permissions(role_permissions)

        return [
            self._build_role_schema(
                role,
                permissions_by_role_id.get(role.id, []),
                permission_names,
            )
            for role in roles
        ]

    async def list_permissions(self) -> list[RBACPermission]:
        permissions = await self.rbac_repository.list_permissions()
        return [RBACPermission.model_validate(permission) for permission in permissions]

    async def create_role(self, role_data: CreateRole) -> RBACRole:
        normalized_name = self._normalize_role_name(role_data.name)
        async with self.unit_of_work:
            if await self.rbac_repository.role_name_exists(normalized_name):
                raise ConflictException(
                    message="Role name already exists",
                    details={"name": normalized_name},
                )
            role = await self.rbac_repository.create_role(name=normalized_name)

        return await self._build_role_response(role)

    async def update_role(self, role_id: int, role_data: UpdateRole) -> RBACRole:
        normalized_name = self._normalize_role_name(role_data.name)
        async with self.unit_of_work:
            role = await self._get_role_or_raise(role_id)
            if normalized_name != role.name and await self.rbac_repository.role_name_exists(
                normalized_name,
                exclude_role_id=role.id,
            ):
                raise ConflictException(
                    message="Role name already exists",
                    details={"name": normalized_name},
                )
            if normalized_name != role.name:
                role = await self.rbac_repository.update_role(role, name=normalized_name)

        return await self._build_role_response(role)

    async def delete_role(self, role_id: int) -> None:
        async with self.unit_of_work:
            role = await self._get_role_or_raise(role_id)
            await self.rbac_repository.delete_role(role.id)

    async def assign_role_permission(
        self,
        role_id: int,
        permission_id: str,
        assignment: SetRolePermission,
    ) -> RBACRolePermission:
        try:
            normalized_scope = normalize_permission_scope(assignment.scope)
        except ValueError as exc:
            raise InvalidInputException(message=str(exc)) from exc

        async with self.unit_of_work:
            role = await self._get_role_or_raise(role_id)
            permission = await self._get_permission_or_raise(permission_id)
            role_permission = await self.rbac_repository.upsert_role_permission(
                role_id=role.id,
                permission_id=permission.id,
                scope=normalized_scope,
            )

        return RBACRolePermission(
            id=permission.id,
            name=permission.name,
            scope=role_permission.scope,
        )

    async def remove_role_permission(self, role_id: int, permission_id: str) -> None:
        async with self.unit_of_work:
            role = await self._get_role_or_raise(role_id)
            permission = await self._get_permission_or_raise(permission_id)
            await self.rbac_repository.delete_role_permission(
                role_id=role.id,
                permission_id=permission.id,
            )

    async def assign_user_role(self, user_id: int, role_id: int) -> UserRoleAssignment:
        async with self.unit_of_work:
            await self._get_user_or_raise(user_id)
            role = await self._get_role_or_raise(role_id)
            await self.rbac_repository.assign_user_role(
                user_id=user_id,
                role_id=role.id,
            )

        return UserRoleAssignment(user_id=user_id, role_id=role.id)

    async def remove_user_role(self, user_id: int, role_id: int) -> None:
        async with self.unit_of_work:
            await self._get_user_or_raise(user_id)
            role = await self._get_role_or_raise(role_id)
            await self.rbac_repository.remove_user_role(
                user_id=user_id,
                role_id=role.id,
            )
