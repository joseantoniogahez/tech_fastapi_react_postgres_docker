from typing import Any, Protocol

from app.core.authorization import PermissionScope
from app.core.authorization.permission_evaluator import PermissionEvaluator, PermissionEvaluatorPort
from app.core.common.records import UserRecord
from app.core.config.settings import AuthSettings
from app.core.db.ports import UnitOfWorkPort
from app.core.errors.services import ConflictError, ForbiddenError, InvalidInputError, UnauthorizedError
from app.core.security.policies import (
    USERNAME_ALLOWED_DESCRIPTION,
    PasswordPolicyError,
    UsernamePolicyError,
    UsernamePolicyErrorCode,
    format_password_policy_messages,
    normalize_username,
    validate_password_policy,
)
from app.core.security.service import Argon2PasswordService, JwtTokenService, PasswordServicePort, TokenServicePort
from app.features.auth.principal import CurrentPrincipal
from app.features.auth.profile_updates import AuthProfileUpdates
from app.features.auth.schemas import (
    AccessTokenResult,
    AuthenticatedUserResult,
    LoginCommand,
    RegisterUserCommand,
    UpdateCurrentUserCommand,
)

PermissionScopeCache = dict[tuple[int, str], str | None]


class AuthRepositoryPort(Protocol):
    async def get_by_username(self, username: str) -> UserRecord | None: ...

    async def username_exists(self, username: str, *, exclude_user_id: int | None = None) -> bool: ...

    async def create_user(self, **kwargs: Any) -> UserRecord: ...

    async def update_user(self, user_id: int, **changes: Any) -> UserRecord: ...

    async def get_rbac_version(self, user_id: int) -> str: ...

    async def get_user_effective_permission_ids(self, user_id: int) -> tuple[str, ...]: ...

    async def get_user_permission_scope(self, user_id: int, permission_id: str) -> str | None: ...

    async def user_has_permission(self, user_id: int, permission_id: str) -> bool: ...


class AuthServicePort(Protocol):
    async def login(self, credentials: LoginCommand) -> AccessTokenResult: ...

    async def register(self, registration: RegisterUserCommand) -> AuthenticatedUserResult: ...

    async def update_current_user(
        self,
        current_user: CurrentPrincipal,
        update_data: UpdateCurrentUserCommand,
    ) -> AuthenticatedUserResult: ...

    async def get_authenticated_user(self, current_user: CurrentPrincipal) -> AuthenticatedUserResult: ...

    async def get_user_from_token(self, token: str) -> CurrentPrincipal: ...

    async def user_has_permission(
        self,
        user_id: int,
        permission_id: str,
        *,
        required_scope: str = PermissionScope.ANY,
        resource_owner_id: int | None = None,
        resource_tenant_id: int | None = None,
        user_tenant_id: int | None = None,
    ) -> bool: ...


class AuthService:
    def __init__(
        self,
        auth_repository: AuthRepositoryPort,
        unit_of_work: UnitOfWorkPort,
        auth_settings: AuthSettings | None = None,
        permission_evaluator: PermissionEvaluatorPort | None = None,
        token_service: TokenServicePort | None = None,
        password_service: PasswordServicePort | None = None,
        permission_scope_cache: PermissionScopeCache | None = None,
    ):
        settings = auth_settings or AuthSettings()
        self.auth_repository = auth_repository
        self.unit_of_work = unit_of_work
        self.permission_evaluator = permission_evaluator or PermissionEvaluator()
        self.token_service = token_service or JwtTokenService(settings)
        self.password_service = password_service or Argon2PasswordService()
        self.permission_scope_cache = permission_scope_cache
        self._profile_updates = AuthProfileUpdates(
            auth_repository=auth_repository,
            unit_of_work=unit_of_work,
            password_service=self.password_service,
            normalize_username=self._normalize_username,
            validate_password_policy=self._validate_password_policy,
        )

    def _normalize_username(self, username: str) -> str:
        try:
            return normalize_username(username)
        except UsernamePolicyError as exc:
            if exc.code is UsernamePolicyErrorCode.REQUIRED:
                raise InvalidInputError(message="Username is required") from exc

            raise InvalidInputError(
                message="Username has invalid format",
                details={
                    "allowed": USERNAME_ALLOWED_DESCRIPTION,
                },
            ) from exc

    def _validate_password_policy(self, password: str, username: str) -> None:
        try:
            validate_password_policy(password, username)
        except PasswordPolicyError as exc:
            raise InvalidInputError(
                message="Password does not meet policy",
                details={"violations": format_password_policy_messages(exc.violations)},
            ) from exc

    async def _authenticate_or_raise(self, credentials: LoginCommand) -> UserRecord:
        username = self._normalize_username(credentials.username)
        user = await self.auth_repository.get_by_username(username)
        if user is None or not self.password_service.verify_password(credentials.password, user.hashed_password):
            raise UnauthorizedError(message="Invalid username or password")

        if user.disabled:
            raise ForbiddenError(message="Inactive user")

        return user

    async def login(self, credentials: LoginCommand) -> AccessTokenResult:
        user = await self._authenticate_or_raise(credentials)
        rbac_version = await self.auth_repository.get_rbac_version(user.id)
        access_token = self.token_service.encode_access_token(
            subject=user.username,
            rbac_version=rbac_version,
        )
        return AccessTokenResult(access_token=access_token)

    async def register(self, registration: RegisterUserCommand) -> AuthenticatedUserResult:
        username = self._normalize_username(registration.username)
        self._validate_password_policy(registration.password, username)

        async with self.unit_of_work:
            if await self.auth_repository.username_exists(username):
                raise ConflictError(
                    message="Username already exists",
                    details={"username": username},
                )

            user = await self.auth_repository.create_user(
                username=username,
                hashed_password=self.password_service.hash_password(registration.password),
                disabled=False,
            )

        return await self._build_authenticated_user_result(user)

    @staticmethod
    def _normalize_permissions(permission_ids: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        return tuple(sorted(set(permission_ids)))

    async def _load_effective_permission_ids(self, user_id: int) -> tuple[str, ...]:
        repository_attributes = getattr(self.auth_repository, "__dict__", {})
        instance_loader = repository_attributes.get("get_user_effective_permission_ids")
        if instance_loader is not None:
            return self._normalize_permissions(await instance_loader(user_id))

        if not hasattr(type(self.auth_repository), "get_user_effective_permission_ids"):
            return ()

        return await self.auth_repository.get_user_effective_permission_ids(user_id)

    async def _build_authenticated_user_result(self, user: UserRecord | CurrentPrincipal) -> AuthenticatedUserResult:
        permission_ids = await self._load_effective_permission_ids(user.id)
        return AuthenticatedUserResult(
            id=user.id,
            username=user.username,
            disabled=user.disabled,
            permissions=permission_ids,
        )

    def _validate_update_request(self, update_data: UpdateCurrentUserCommand) -> None:
        self._profile_updates.validate_update_request(update_data)

    async def _build_username_change(
        self,
        current_user: UserRecord,
        username: str | None,
    ) -> tuple[str, dict[str, str]]:
        return await self._profile_updates.build_username_change(current_user, username)

    def _build_password_change(
        self,
        current_user: UserRecord,
        update_data: UpdateCurrentUserCommand,
        normalized_username: str,
    ) -> dict[str, str]:
        return self._profile_updates.build_password_change(current_user, update_data, normalized_username)

    async def _persist_user_changes(self, current_user: UserRecord, changes: dict[str, str]) -> UserRecord:
        return await self._profile_updates.persist_user_changes(current_user, changes)

    async def update_current_user(
        self,
        current_user: CurrentPrincipal,
        update_data: UpdateCurrentUserCommand,
    ) -> AuthenticatedUserResult:
        persisted_user = await self.auth_repository.get_by_username(current_user.username)
        if persisted_user is None:
            raise UnauthorizedError(message="Could not validate credentials")

        updated_user = await self._profile_updates.update_current_user(persisted_user, update_data)
        return await self._build_authenticated_user_result(updated_user)

    async def get_authenticated_user(self, current_user: CurrentPrincipal) -> AuthenticatedUserResult:
        return await self._build_authenticated_user_result(current_user)

    async def get_user_from_token(self, token: str) -> CurrentPrincipal:
        payload = self.token_service.decode_access_token(token)
        if payload is None:
            raise UnauthorizedError(message="Could not validate credentials")

        user = await self.auth_repository.get_by_username(payload.sub)
        if user is None:
            raise UnauthorizedError(message="Could not validate credentials")

        current_rbac_version = await self.auth_repository.get_rbac_version(user.id)
        if payload.rbac_version != current_rbac_version:
            raise UnauthorizedError(message="Could not validate credentials")

        return CurrentPrincipal.from_domain(user)

    async def _get_granted_scope(self, *, user_id: int, permission_id: str) -> str | None:
        if self.permission_scope_cache is None:
            return await self.auth_repository.get_user_permission_scope(
                user_id=user_id,
                permission_id=permission_id,
            )

        cache_key = (user_id, permission_id)
        if cache_key in self.permission_scope_cache:
            return self.permission_scope_cache[cache_key]

        granted_scope = await self.auth_repository.get_user_permission_scope(
            user_id=user_id,
            permission_id=permission_id,
        )
        self.permission_scope_cache[cache_key] = granted_scope
        return granted_scope

    async def user_has_permission(
        self,
        user_id: int,
        permission_id: str,
        *,
        required_scope: str = PermissionScope.ANY,
        resource_owner_id: int | None = None,
        resource_tenant_id: int | None = None,
        user_tenant_id: int | None = None,
    ) -> bool:
        normalized_required_scope = self.permission_evaluator.normalize_required_scope(required_scope)
        granted_scope = await self._get_granted_scope(
            user_id=user_id,
            permission_id=permission_id,
        )
        return self.permission_evaluator.is_granted_scope_allowed(
            granted_scope=granted_scope,
            required_scope=normalized_required_scope,
            user_id=user_id,
            resource_owner_id=resource_owner_id,
            user_tenant_id=user_tenant_id,
            resource_tenant_id=resource_tenant_id,
        )
