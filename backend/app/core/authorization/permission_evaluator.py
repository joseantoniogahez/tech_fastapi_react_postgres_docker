from typing import Protocol

from app.core.authorization import PERMISSION_SCOPE_RANK, PermissionScope, normalize_permission_scope


class PermissionEvaluatorPort(Protocol):
    def normalize_required_scope(self, required_scope: str) -> str: ...

    def is_granted_scope_allowed(
        self,
        *,
        granted_scope: str | None,
        required_scope: str,
        user_id: int,
        resource_owner_id: int | None,
        user_tenant_id: int | None,
        resource_tenant_id: int | None,
    ) -> bool: ...


class PermissionEvaluator:
    def normalize_required_scope(self, required_scope: str) -> str:
        return normalize_permission_scope(required_scope)

    @staticmethod
    def _is_valid_scope(scope: str) -> bool:
        return scope in PERMISSION_SCOPE_RANK

    @staticmethod
    def _is_owner_match(*, user_id: int, resource_owner_id: int | None) -> bool:
        return resource_owner_id is not None and resource_owner_id == user_id

    @staticmethod
    def _is_tenant_match(*, user_tenant_id: int | None, resource_tenant_id: int | None) -> bool:
        return user_tenant_id is not None and resource_tenant_id is not None and user_tenant_id == resource_tenant_id

    def _scope_satisfies_requirement(
        self,
        *,
        granted_scope: str,
        required_scope: str,
        user_id: int,
        resource_owner_id: int | None,
        user_tenant_id: int | None,
        resource_tenant_id: int | None,
    ) -> bool:
        if PERMISSION_SCOPE_RANK[granted_scope] < PERMISSION_SCOPE_RANK[required_scope]:
            return False

        owner_match = self._is_owner_match(user_id=user_id, resource_owner_id=resource_owner_id)
        tenant_match = self._is_tenant_match(user_tenant_id=user_tenant_id, resource_tenant_id=resource_tenant_id)

        if required_scope == PermissionScope.ANY:
            return granted_scope == PermissionScope.ANY

        if required_scope == PermissionScope.TENANT:
            return granted_scope == PermissionScope.ANY or tenant_match

        if required_scope == PermissionScope.OWN:
            if granted_scope == PermissionScope.ANY:
                return True
            if granted_scope == PermissionScope.TENANT:
                # Tenant grants can satisfy own-scoped checks when tenant or owner context matches.
                return tenant_match or owner_match
            return owner_match

        return False

    def is_granted_scope_allowed(
        self,
        *,
        granted_scope: str | None,
        required_scope: str,
        user_id: int,
        resource_owner_id: int | None,
        user_tenant_id: int | None,
        resource_tenant_id: int | None,
    ) -> bool:
        if granted_scope is None:
            return False
        if not self._is_valid_scope(granted_scope):
            return False

        return self._scope_satisfies_requirement(
            granted_scope=granted_scope,
            required_scope=required_scope,
            user_id=user_id,
            resource_owner_id=resource_owner_id,
            user_tenant_id=user_tenant_id,
            resource_tenant_id=resource_tenant_id,
        )
