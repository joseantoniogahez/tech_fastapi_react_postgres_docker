from typing import Protocol

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
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

from .operations import RBACEntityLookup, RBACRoleOperations, RBACUserRoleAssignments


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
    async def list_roles(self) -> list[RoleResult]: ...

    async def list_permissions(self) -> list[PermissionResult]: ...

    async def create_role(self, role_data: CreateRoleCommand) -> RoleResult: ...

    async def update_role(self, role_id: int, role_data: UpdateRoleCommand) -> RoleResult: ...

    async def delete_role(self, role_id: int) -> None: ...

    async def assign_role_permission(
        self,
        role_id: int,
        permission_id: str,
        assignment: SetRolePermissionCommand,
    ) -> RolePermissionResult: ...

    async def remove_role_permission(self, role_id: int, permission_id: str) -> None: ...

    async def assign_user_role(self, user_id: int, role_id: int) -> UserRoleAssignmentResult: ...

    async def remove_user_role(self, user_id: int, role_id: int) -> None: ...


class RBACService:
    def __init__(
        self,
        rbac_repository: RBACRepositoryPort,
        unit_of_work: UnitOfWorkPort,
    ):
        entity_lookup = RBACEntityLookup(rbac_repository)
        self._role_operations = RBACRoleOperations(
            rbac_repository=rbac_repository,
            unit_of_work=unit_of_work,
            entity_lookup=entity_lookup,
        )
        self._user_role_assignments = RBACUserRoleAssignments(
            rbac_repository=rbac_repository,
            unit_of_work=unit_of_work,
            entity_lookup=entity_lookup,
        )

    async def list_roles(self) -> list[RoleResult]:
        return await self._role_operations.list_roles()

    async def list_permissions(self) -> list[PermissionResult]:
        return await self._role_operations.list_permissions()

    async def create_role(self, role_data: CreateRoleCommand) -> RoleResult:
        return await self._role_operations.create_role(role_data)

    async def update_role(self, role_id: int, role_data: UpdateRoleCommand) -> RoleResult:
        return await self._role_operations.update_role(role_id, role_data)

    async def delete_role(self, role_id: int) -> None:
        await self._role_operations.delete_role(role_id)

    async def assign_role_permission(
        self,
        role_id: int,
        permission_id: str,
        assignment: SetRolePermissionCommand,
    ) -> RolePermissionResult:
        return await self._role_operations.assign_role_permission(
            role_id,
            permission_id,
            assignment,
        )

    async def remove_role_permission(self, role_id: int, permission_id: str) -> None:
        await self._role_operations.remove_role_permission(role_id, permission_id)

    async def assign_user_role(self, user_id: int, role_id: int) -> UserRoleAssignmentResult:
        return await self._user_role_assignments.assign_user_role(user_id, role_id)

    async def remove_user_role(self, user_id: int, role_id: int) -> None:
        await self._user_role_assignments.remove_user_role(user_id, role_id)
