from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.authorization import normalize_permission_scope
from app.core.common.records import (
    PermissionRecord,
    RoleInheritanceRecord,
    RolePermissionRecord,
    RoleRecord,
    UserRecord,
)
from app.core.db.ports import UnitOfWorkPort
from app.core.errors.services import ConflictError, InvalidInputError, NotFoundError, UnauthorizedError
from app.core.security.policies import (
    USERNAME_ALLOWED_DESCRIPTION,
    PasswordPolicyError,
    UsernamePolicyError,
    UsernamePolicyErrorCode,
    format_password_policy_messages,
    normalize_username,
    validate_password_policy,
)
from app.core.security.service import Argon2PasswordService, PasswordServicePort
from app.features.rbac.effective_permissions import resolve_effective_role_permissions
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
from app.features.rbac.service_mappers import (
    build_permission_name_map,
    group_parent_role_ids,
    group_role_permissions,
    normalize_role_name,
    to_admin_user_result,
    to_assigned_role_results,
    to_assigned_user_results,
    to_permission_results,
    to_role_permission_result,
    to_role_result,
)

if TYPE_CHECKING:
    from app.features.rbac.service import RBACRepositoryPort


class RBACEntityLookup:
    def __init__(self, rbac_repository: RBACRepositoryPort):
        self._rbac_repository = rbac_repository

    async def get_role_or_raise(self, role_id: int) -> RoleRecord:
        role = await self._rbac_repository.get_role(role_id)
        if role is None:
            raise NotFoundError(message=f"Role {role_id} not found", details={"id": role_id})
        return role

    async def get_permission_or_raise(self, permission_id: str) -> PermissionRecord:
        permission = await self._rbac_repository.get_permission(permission_id)
        if permission is None:
            raise NotFoundError(
                message=f"Permission {permission_id} not found",
                details={"permission_id": permission_id},
            )
        return permission

    async def get_user_or_raise(self, user_id: int) -> UserRecord:
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

    async def _list_effective_role_permissions(
        self,
        *,
        role_ids: tuple[int, ...] | None = None,
        role_inheritances: list[RoleInheritanceRecord] | None = None,
    ) -> list[RolePermissionRecord]:
        role_permissions = await self._rbac_repository.list_role_permissions()
        resolved_role_inheritances = role_inheritances
        if resolved_role_inheritances is None:
            resolved_role_inheritances = await self._rbac_repository.list_role_inheritances()
        return resolve_effective_role_permissions(
            role_permissions=role_permissions,
            role_inheritances=resolved_role_inheritances,
            role_ids=role_ids,
        )

    async def _build_role_response(self, role: RoleRecord) -> RoleResult:
        permissions = await self._rbac_repository.list_permissions()
        permission_names = build_permission_name_map(permissions)
        role_inheritances = await self._rbac_repository.list_role_inheritances()
        role_permissions = await self._list_effective_role_permissions(
            role_ids=(role.id,),
            role_inheritances=role_inheritances,
        )
        parent_role_ids_by_role_id = group_parent_role_ids(role_inheritances)
        return to_role_result(
            role,
            role_permissions,
            permission_names,
            parent_role_ids=parent_role_ids_by_role_id.get(role.id, ()),
        )

    async def list_roles(self) -> list[RoleResult]:
        roles = await self._rbac_repository.list_roles()
        if not roles:
            return []

        permissions = await self._rbac_repository.list_permissions()
        permission_names = build_permission_name_map(permissions)
        role_inheritances = await self._rbac_repository.list_role_inheritances()
        role_permissions = await self._list_effective_role_permissions(
            role_ids=tuple(role.id for role in roles),
            role_inheritances=role_inheritances,
        )
        permissions_by_role_id = group_role_permissions(role_permissions)
        parent_role_ids_by_role_id = group_parent_role_ids(role_inheritances)

        return [
            to_role_result(
                role,
                permissions_by_role_id.get(role.id, []),
                permission_names,
                parent_role_ids=parent_role_ids_by_role_id.get(role.id, ()),
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
                role = await self._rbac_repository.update_role(role.id, name=normalized_name)

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

    @staticmethod
    def _role_reaches_target(
        *,
        parents_by_role_id: dict[int, tuple[int, ...]],
        start_role_id: int,
        target_role_id: int,
    ) -> bool:
        pending_role_ids = [start_role_id]
        visited_role_ids: set[int] = set()
        while pending_role_ids:
            role_id = pending_role_ids.pop()
            if role_id == target_role_id:
                return True
            if role_id in visited_role_ids:
                continue
            visited_role_ids.add(role_id)
            pending_role_ids.extend(parents_by_role_id.get(role_id, ()))
        return False

    async def assign_role_inheritance(self, role_id: int, parent_role_id: int) -> None:
        if role_id == parent_role_id:
            raise InvalidInputError(message="Role cannot inherit from itself")

        async with self._unit_of_work:
            role = await self._entity_lookup.get_role_or_raise(role_id)
            parent_role = await self._entity_lookup.get_role_or_raise(parent_role_id)
            role_inheritances = await self._rbac_repository.list_role_inheritances()
            existing_links = {(link.role_id, link.parent_role_id) for link in role_inheritances}
            if (role.id, parent_role.id) in existing_links:
                return

            parents_by_role_id: dict[int, tuple[int, ...]] = {}
            for role_inheritance in role_inheritances:
                current_parents = parents_by_role_id.get(role_inheritance.role_id, ())
                parents_by_role_id[role_inheritance.role_id] = current_parents + (role_inheritance.parent_role_id,)

            if self._role_reaches_target(
                parents_by_role_id=parents_by_role_id,
                start_role_id=parent_role.id,
                target_role_id=role.id,
            ):
                raise ConflictError(
                    message="Role inheritance cycle detected",
                    details={"role_id": role.id, "parent_role_id": parent_role.id},
                )

            await self._rbac_repository.assign_role_inheritance(
                role_id=role.id,
                parent_role_id=parent_role.id,
            )

    async def remove_role_inheritance(self, role_id: int, parent_role_id: int) -> None:
        async with self._unit_of_work:
            role = await self._entity_lookup.get_role_or_raise(role_id)
            parent_role = await self._entity_lookup.get_role_or_raise(parent_role_id)
            await self._rbac_repository.remove_role_inheritance(
                role_id=role.id,
                parent_role_id=parent_role.id,
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

    async def list_user_roles(self, user_id: int) -> list[AssignedRoleResult]:
        await self._entity_lookup.get_user_or_raise(user_id)
        roles = await self._rbac_repository.list_user_roles(user_id=user_id)
        return to_assigned_role_results(roles)

    async def list_role_users(self, role_id: int) -> list[AssignedUserResult]:
        await self._entity_lookup.get_role_or_raise(role_id)
        users = await self._rbac_repository.list_role_users(role_id=role_id)
        return to_assigned_user_results(users)


class RBACUserManagement:
    def __init__(
        self,
        *,
        rbac_repository: RBACRepositoryPort,
        unit_of_work: UnitOfWorkPort,
        entity_lookup: RBACEntityLookup,
        password_service: PasswordServicePort | None = None,
    ):
        self._rbac_repository = rbac_repository
        self._unit_of_work = unit_of_work
        self._entity_lookup = entity_lookup
        self._password_service = password_service or Argon2PasswordService()

    @staticmethod
    def _normalize_role_ids(role_ids: list[int]) -> list[int]:
        normalized_role_ids = sorted(set(role_ids))
        invalid_role_ids = [role_id for role_id in normalized_role_ids if role_id < 1]
        if invalid_role_ids:
            raise InvalidInputError(
                message="role_ids must contain positive integers",
                details={"role_ids": invalid_role_ids},
            )
        return normalized_role_ids

    @staticmethod
    def _normalize_username_or_raise(username: str) -> str:
        try:
            return normalize_username(username)
        except UsernamePolicyError as exc:
            if exc.code is UsernamePolicyErrorCode.REQUIRED:
                raise InvalidInputError(message="Username is required") from exc

            raise InvalidInputError(
                message="Username has invalid format",
                details={"allowed": USERNAME_ALLOWED_DESCRIPTION},
            ) from exc

    @staticmethod
    def _validate_password_or_raise(password: str, username: str) -> None:
        try:
            validate_password_policy(password, username)
        except PasswordPolicyError as exc:
            raise InvalidInputError(
                message="Password does not meet policy",
                details={"violations": format_password_policy_messages(exc.violations)},
            ) from exc

    async def _build_admin_user_result(self, user_id: int) -> AdminUserResult:
        user = await self._entity_lookup.get_user_or_raise(user_id)
        role_ids = await self._rbac_repository.list_user_role_ids(user_id=user_id)
        return to_admin_user_result(user, role_ids=role_ids)

    async def _validate_roles_exist(self, role_ids: list[int]) -> None:
        for role_id in role_ids:
            await self._entity_lookup.get_role_or_raise(role_id)

    async def list_users(self) -> list[AdminUserResult]:
        users = await self._rbac_repository.list_users()
        user_results: list[AdminUserResult] = []
        for user in users:
            role_ids = await self._rbac_repository.list_user_role_ids(user_id=user.id)
            user_results.append(to_admin_user_result(user, role_ids=role_ids))
        return user_results

    async def get_user(self, user_id: int) -> AdminUserResult:
        return await self._build_admin_user_result(user_id)

    async def create_user(self, user_data: CreateAdminUserCommand) -> AdminUserResult:
        normalized_username = self._normalize_username_or_raise(user_data.username)
        self._validate_password_or_raise(user_data.password, normalized_username)
        normalized_role_ids = self._normalize_role_ids(user_data.role_ids)

        async with self._unit_of_work:
            if await self._rbac_repository.username_exists(normalized_username):
                raise ConflictError(
                    message="Username already exists",
                    details={"username": normalized_username},
                )

            await self._validate_roles_exist(normalized_role_ids)
            user = await self._rbac_repository.create_user(
                username=normalized_username,
                hashed_password=self._password_service.hash_password(user_data.password),
                disabled=False,
            )
            for role_id in normalized_role_ids:
                await self._rbac_repository.assign_user_role(user_id=user.id, role_id=role_id)

        return await self._build_admin_user_result(user.id)

    @staticmethod
    def _validate_update_payload(user_data: UpdateAdminUserCommand) -> None:
        if user_data.current_password and user_data.new_password is None:
            raise InvalidInputError(message="new_password is required when current_password is provided")
        if user_data.new_password and user_data.current_password is None:
            raise InvalidInputError(message="current_password is required to update password")
        if (
            user_data.username is None
            and user_data.new_password is None
            and user_data.disabled is None
            and user_data.role_ids is None
        ):
            raise InvalidInputError(message="At least one field must be provided to update the user")

    async def _apply_username_update(
        self,
        *,
        user: UserRecord,
        requested_username: str | None,
        changes: dict[str, object],
    ) -> str:
        normalized_username = user.username
        if requested_username is None:
            return normalized_username

        normalized_username = self._normalize_username_or_raise(requested_username)
        if normalized_username == user.username:
            return normalized_username

        if await self._rbac_repository.username_exists(normalized_username, exclude_user_id=user.id):
            raise ConflictError(
                message="Username already exists",
                details={"username": normalized_username},
            )
        changes["username"] = normalized_username
        return normalized_username

    def _apply_password_update(
        self,
        *,
        user: UserRecord,
        current_password: str | None,
        new_password: str | None,
        normalized_username: str,
        changes: dict[str, object],
    ) -> None:
        if new_password is None:
            return

        if current_password is None:
            raise InvalidInputError(message="current_password is required to update password")

        if not self._password_service.verify_password(current_password, user.hashed_password):
            raise UnauthorizedError(message="Current password is invalid")
        if self._password_service.verify_password(new_password, user.hashed_password):
            raise InvalidInputError(message="New password must be different from current password")
        self._validate_password_or_raise(new_password, normalized_username)
        changes["hashed_password"] = self._password_service.hash_password(new_password)

    @staticmethod
    def _apply_disabled_update(
        *,
        user: UserRecord,
        requested_disabled: bool | None,
        changes: dict[str, object],
    ) -> None:
        if requested_disabled is None or requested_disabled == user.disabled:
            return
        changes["disabled"] = requested_disabled

    async def _apply_role_ids_update(
        self,
        *,
        user_id: int,
        role_ids: list[int] | None,
    ) -> None:
        if role_ids is None:
            return

        normalized_role_ids = self._normalize_role_ids(role_ids)
        await self._validate_roles_exist(normalized_role_ids)

        existing_role_ids = set(await self._rbac_repository.list_user_role_ids(user_id=user_id))
        target_role_ids = set(normalized_role_ids)

        for role_id in sorted(existing_role_ids - target_role_ids):
            await self._rbac_repository.remove_user_role(user_id=user_id, role_id=role_id)
        for role_id in sorted(target_role_ids - existing_role_ids):
            await self._rbac_repository.assign_user_role(user_id=user_id, role_id=role_id)

    async def update_user(self, user_id: int, user_data: UpdateAdminUserCommand) -> AdminUserResult:
        self._validate_update_payload(user_data)

        async with self._unit_of_work:
            user = await self._entity_lookup.get_user_or_raise(user_id)
            changes: dict[str, object] = {}
            normalized_username = await self._apply_username_update(
                user=user,
                requested_username=user_data.username,
                changes=changes,
            )
            self._apply_password_update(
                user=user,
                current_password=user_data.current_password,
                new_password=user_data.new_password,
                normalized_username=normalized_username,
                changes=changes,
            )
            self._apply_disabled_update(
                user=user,
                requested_disabled=user_data.disabled,
                changes=changes,
            )
            if changes:
                await self._rbac_repository.update_user(user.id, **changes)
            await self._apply_role_ids_update(user_id=user.id, role_ids=user_data.role_ids)

        return await self._build_admin_user_result(user_id)

    async def delete_user(self, user_id: int) -> None:
        async with self._unit_of_work:
            user = await self._entity_lookup.get_user_or_raise(user_id)
            if user.disabled:
                return
            await self._rbac_repository.update_user(user.id, disabled=True)
