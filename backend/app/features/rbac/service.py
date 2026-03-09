from typing import Protocol

from app.core.common.records import (
    PermissionRecord,
    RoleInheritanceRecord,
    RolePermissionRecord,
    RoleRecord,
    UserRecord,
)
from app.core.db.ports import UnitOfWorkPort
from app.features.rbac.operations import (
    RBACEntityLookup,
    RBACRoleOperations,
    RBACUserManagement,
    RBACUserRoleAssignments,
)
from app.features.rbac.schemas import (
    AdminUserResult,
    AssignedRoleResult,
    AssignedUserResult,
    CreateAdminUserCommand,
    CreateRoleCommand,
    PermissionResult,
    RolePermissionResult,
    RoleResult,
    SetRolePermissionCommand,
    UpdateAdminUserCommand,
    UpdateRoleCommand,
    UserRoleAssignmentResult,
)


class RBACRepositoryPort(Protocol):
    async def list_users(self) -> list[UserRecord]: ...

    async def list_roles(self) -> list[RoleRecord]: ...

    async def list_permissions(self) -> list[PermissionRecord]: ...

    async def list_role_permissions(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
    ) -> list[RolePermissionRecord]: ...

    async def list_role_inheritances(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
    ) -> list[RoleInheritanceRecord]: ...

    async def get_role(self, role_id: int) -> RoleRecord | None: ...

    async def role_name_exists(self, name: str, *, exclude_role_id: int | None = None) -> bool: ...

    async def create_role(self, *, name: str) -> RoleRecord: ...

    async def update_role(self, role_id: int, *, name: str) -> RoleRecord: ...

    async def delete_role(self, role_id: int) -> bool: ...

    async def get_permission(self, permission_id: str) -> PermissionRecord | None: ...

    async def upsert_role_permission(
        self,
        *,
        role_id: int,
        permission_id: str,
        scope: str,
    ) -> RolePermissionRecord: ...

    async def delete_role_permission(self, *, role_id: int, permission_id: str) -> bool: ...

    async def get_user(self, user_id: int) -> UserRecord | None: ...

    async def username_exists(self, username: str, *, exclude_user_id: int | None = None) -> bool: ...

    async def create_user(self, **kwargs: object) -> UserRecord: ...

    async def update_user(self, user_id: int, **changes: object) -> UserRecord: ...

    async def list_user_role_ids(self, *, user_id: int) -> list[int]: ...

    async def assign_user_role(self, *, user_id: int, role_id: int) -> bool: ...

    async def remove_user_role(self, *, user_id: int, role_id: int) -> bool: ...

    async def list_user_roles(self, *, user_id: int) -> list[RoleRecord]: ...

    async def list_role_users(self, *, role_id: int) -> list[UserRecord]: ...

    async def assign_role_inheritance(self, *, role_id: int, parent_role_id: int) -> bool: ...

    async def remove_role_inheritance(self, *, role_id: int, parent_role_id: int) -> bool: ...


class RBACServicePort(Protocol):
    async def list_users(self) -> list[AdminUserResult]: ...

    async def get_user(self, user_id: int) -> AdminUserResult: ...

    async def create_user(self, user_data: CreateAdminUserCommand) -> AdminUserResult: ...

    async def update_user(self, user_id: int, user_data: UpdateAdminUserCommand) -> AdminUserResult: ...

    async def delete_user(self, user_id: int) -> None: ...

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

    async def assign_role_inheritance(self, role_id: int, parent_role_id: int) -> None: ...

    async def remove_role_inheritance(self, role_id: int, parent_role_id: int) -> None: ...

    async def assign_user_role(self, user_id: int, role_id: int) -> UserRoleAssignmentResult: ...

    async def remove_user_role(self, user_id: int, role_id: int) -> None: ...

    async def list_user_roles(self, user_id: int) -> list[AssignedRoleResult]: ...

    async def list_role_users(self, role_id: int) -> list[AssignedUserResult]: ...


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
        self._user_management = RBACUserManagement(
            rbac_repository=rbac_repository,
            unit_of_work=unit_of_work,
            entity_lookup=entity_lookup,
        )
        self._user_role_assignments = RBACUserRoleAssignments(
            rbac_repository=rbac_repository,
            unit_of_work=unit_of_work,
            entity_lookup=entity_lookup,
        )

    async def list_users(self) -> list[AdminUserResult]:
        return await self._user_management.list_users()

    async def get_user(self, user_id: int) -> AdminUserResult:
        return await self._user_management.get_user(user_id)

    async def create_user(self, user_data: CreateAdminUserCommand) -> AdminUserResult:
        return await self._user_management.create_user(user_data)

    async def update_user(self, user_id: int, user_data: UpdateAdminUserCommand) -> AdminUserResult:
        return await self._user_management.update_user(user_id, user_data)

    async def delete_user(self, user_id: int) -> None:
        await self._user_management.delete_user(user_id)

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

    async def assign_role_inheritance(self, role_id: int, parent_role_id: int) -> None:
        await self._role_operations.assign_role_inheritance(role_id, parent_role_id)

    async def remove_role_inheritance(self, role_id: int, parent_role_id: int) -> None:
        await self._role_operations.remove_role_inheritance(role_id, parent_role_id)

    async def assign_user_role(self, user_id: int, role_id: int) -> UserRoleAssignmentResult:
        return await self._user_role_assignments.assign_user_role(user_id, role_id)

    async def remove_user_role(self, user_id: int, role_id: int) -> None:
        await self._user_role_assignments.remove_user_role(user_id, role_id)

    async def list_user_roles(self, user_id: int) -> list[AssignedRoleResult]:
        return await self._user_role_assignments.list_user_roles(user_id)

    async def list_role_users(self, role_id: int) -> list[AssignedUserResult]:
        return await self._user_role_assignments.list_role_users(role_id)
