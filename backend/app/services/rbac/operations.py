from __future__ import annotations

from typing import TYPE_CHECKING

from app.authorization import normalize_permission_scope
from app.exceptions.services import ConflictError, InvalidInputError, NotFoundError
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.schemas.application.rbac import (
    CreateRoleCommand,
    PermissionResult,
    RolePermissionResult,
    RoleResult,
    SetRolePermissionCommand,
    UpdateRoleCommand,
    UserRoleAssignmentResult,
)
from app.services import UnitOfWorkPort

from .mappers import (
    build_permission_name_map,
    group_role_permissions,
    normalize_role_name,
    to_permission_results,
    to_role_permission_result,
    to_role_result,
)

if TYPE_CHECKING:
    from .service import RBACRepositoryPort


class RBACEntityLookup:
    def __init__(self, rbac_repository: RBACRepositoryPort):
        self._rbac_repository = rbac_repository

    async def get_role_or_raise(self, role_id: int) -> Role:
        role = await self._rbac_repository.get_role(role_id)
        if role is None:
            raise NotFoundError(message=f"Role {role_id} not found", details={"id": role_id})
        return role

    async def get_permission_or_raise(self, permission_id: str) -> Permission:
        permission = await self._rbac_repository.get_permission(permission_id)
        if permission is None:
            raise NotFoundError(
                message=f"Permission {permission_id} not found",
                details={"permission_id": permission_id},
            )
        return permission

    async def get_user_or_raise(self, user_id: int) -> User:
        user = await self._rbac_repository.get_user(user_id)
        if user is None:
            raise NotFoundError(message=f"User {user_id} not found", details={"id": user_id})
        return user


class RBACRoleOperations:
    def __init__(
        self,
        *,
        rbac_repository: RBACRepositoryPort,
        unit_of_work: UnitOfWorkPort,
        entity_lookup: RBACEntityLookup,
    ):
        self._rbac_repository = rbac_repository
        self._unit_of_work = unit_of_work
        self._entity_lookup = entity_lookup

    async def _build_role_response(self, role: Role) -> RoleResult:
        permissions = await self._rbac_repository.list_permissions()
        permission_names = build_permission_name_map(permissions)
        role_permissions = await self._rbac_repository.list_role_permissions(role_ids=(role.id,))
        return to_role_result(role, role_permissions, permission_names)

    async def list_roles(self) -> list[RoleResult]:
        roles = await self._rbac_repository.list_roles()
        if not roles:
            return []

        permissions = await self._rbac_repository.list_permissions()
        permission_names = build_permission_name_map(permissions)
        role_permissions = await self._rbac_repository.list_role_permissions(role_ids=tuple(role.id for role in roles))
        permissions_by_role_id = group_role_permissions(role_permissions)

        return [
            to_role_result(
                role,
                permissions_by_role_id.get(role.id, []),
                permission_names,
            )
            for role in roles
        ]

    async def list_permissions(self) -> list[PermissionResult]:
        permissions = await self._rbac_repository.list_permissions()
        return to_permission_results(permissions)

    async def create_role(self, role_data: CreateRoleCommand) -> RoleResult:
        normalized_name = normalize_role_name(role_data.name)
        async with self._unit_of_work:
            if await self._rbac_repository.role_name_exists(normalized_name):
                raise ConflictError(
                    message="Role name already exists",
                    details={"name": normalized_name},
                )
            role = await self._rbac_repository.create_role(name=normalized_name)

        return await self._build_role_response(role)

    async def update_role(self, role_id: int, role_data: UpdateRoleCommand) -> RoleResult:
        normalized_name = normalize_role_name(role_data.name)
        async with self._unit_of_work:
            role = await self._entity_lookup.get_role_or_raise(role_id)
            if normalized_name != role.name and await self._rbac_repository.role_name_exists(
                normalized_name,
                exclude_role_id=role.id,
            ):
                raise ConflictError(
                    message="Role name already exists",
                    details={"name": normalized_name},
                )
            if normalized_name != role.name:
                role = await self._rbac_repository.update_role(role, name=normalized_name)

        return await self._build_role_response(role)

    async def delete_role(self, role_id: int) -> None:
        async with self._unit_of_work:
            role = await self._entity_lookup.get_role_or_raise(role_id)
            await self._rbac_repository.delete_role(role.id)

    async def assign_role_permission(
        self,
        role_id: int,
        permission_id: str,
        assignment: SetRolePermissionCommand,
    ) -> RolePermissionResult:
        try:
            normalized_scope = normalize_permission_scope(assignment.scope)
        except ValueError as exc:
            raise InvalidInputError(message=str(exc)) from exc

        async with self._unit_of_work:
            role = await self._entity_lookup.get_role_or_raise(role_id)
            permission = await self._entity_lookup.get_permission_or_raise(permission_id)
            role_permission = await self._rbac_repository.upsert_role_permission(
                role_id=role.id,
                permission_id=permission.id,
                scope=normalized_scope,
            )

        return to_role_permission_result(
            role_permission,
            {permission.id: permission.name},
        )

    async def remove_role_permission(self, role_id: int, permission_id: str) -> None:
        async with self._unit_of_work:
            role = await self._entity_lookup.get_role_or_raise(role_id)
            permission = await self._entity_lookup.get_permission_or_raise(permission_id)
            await self._rbac_repository.delete_role_permission(
                role_id=role.id,
                permission_id=permission.id,
            )


class RBACUserRoleAssignments:
    def __init__(
        self,
        *,
        rbac_repository: RBACRepositoryPort,
        unit_of_work: UnitOfWorkPort,
        entity_lookup: RBACEntityLookup,
    ):
        self._rbac_repository = rbac_repository
        self._unit_of_work = unit_of_work
        self._entity_lookup = entity_lookup

    async def assign_user_role(self, user_id: int, role_id: int) -> UserRoleAssignmentResult:
        async with self._unit_of_work:
            await self._entity_lookup.get_user_or_raise(user_id)
            role = await self._entity_lookup.get_role_or_raise(role_id)
            await self._rbac_repository.assign_user_role(
                user_id=user_id,
                role_id=role.id,
            )

        return UserRoleAssignmentResult(user_id=user_id, role_id=role.id)

    async def remove_user_role(self, user_id: int, role_id: int) -> None:
        async with self._unit_of_work:
            await self._entity_lookup.get_user_or_raise(user_id)
            role = await self._entity_lookup.get_role_or_raise(role_id)
            await self._rbac_repository.remove_user_role(
                user_id=user_id,
                role_id=role.id,
            )
