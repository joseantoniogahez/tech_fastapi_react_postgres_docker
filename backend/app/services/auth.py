from typing import Any, Protocol

from app.const.permission import PermissionScope
from app.const.settings import AuthSettings
from app.exceptions.services import ConflictException, ForbiddenException, InvalidInputException, UnauthorizedException
from app.models.user import User
from app.schemas.auth import AuthenticatedUser, Credentials, RegisterUser, Token, UpdateCurrentUser
from app.security.policies import (
    USERNAME_ALLOWED_DESCRIPTION,
    PasswordPolicyError,
    UsernamePolicyError,
    UsernamePolicyErrorCode,
    format_password_policy_messages,
    normalize_username,
    validate_password_policy,
)
from app.services import UnitOfWorkPort
from app.services.password_service import Argon2PasswordService, PasswordServicePort
from app.services.permission_evaluator import PermissionEvaluator, PermissionEvaluatorPort
from app.services.token_service import JwtTokenService, TokenServicePort


class AuthRepositoryPort(Protocol):
    async def get_by_username(self, username: str) -> User | None: ...

    async def username_exists(self, username: str, *, exclude_user_id: int | None = None) -> bool: ...

    async def create(self, **kwargs: Any) -> User: ...

    async def update(self, entity: User, **changes: Any) -> User: ...

    async def get_user_permission_scope(self, user_id: int, permission_id: str) -> str | None: ...

    async def user_has_permission(self, user_id: int, permission_id: str) -> bool: ...


class AuthServicePort(Protocol):
    async def login(self, credentials: Credentials) -> Token: ...

    async def register(self, registration: RegisterUser) -> AuthenticatedUser: ...

    async def update_current_user(self, current_user: User, update_data: UpdateCurrentUser) -> AuthenticatedUser: ...

    async def get_user_from_token(self, token: str) -> User: ...

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
    ):
        settings = auth_settings or AuthSettings()
        self.auth_repository = auth_repository
        self.unit_of_work = unit_of_work
        self.permission_evaluator = permission_evaluator or PermissionEvaluator()
        self.token_service = token_service or JwtTokenService(settings)
        self.password_service = password_service or Argon2PasswordService()

    def _normalize_username(self, username: str) -> str:
        try:
            return normalize_username(username)
        except UsernamePolicyError as exc:
            if exc.code is UsernamePolicyErrorCode.REQUIRED:
                raise InvalidInputException(message="Username is required") from exc

            raise InvalidInputException(
                message="Username has invalid format",
                details={
                    "allowed": USERNAME_ALLOWED_DESCRIPTION,
                },
            ) from exc

    def _validate_password_policy(self, password: str, username: str) -> None:
        try:
            validate_password_policy(password, username)
        except PasswordPolicyError as exc:
            raise InvalidInputException(
                message="Password does not meet policy",
                details={"violations": format_password_policy_messages(exc.violations)},
            ) from exc

    async def _authenticate_or_raise(self, credentials: Credentials) -> User:
        username = self._normalize_username(credentials.username)
        user = await self.auth_repository.get_by_username(username)
        if user is None or not self.password_service.verify_password(credentials.password, user.hashed_password):
            raise UnauthorizedException(message="Invalid username or password")

        if user.disabled:
            raise ForbiddenException(message="Inactive user")

        return user

    async def login(self, credentials: Credentials) -> Token:
        user = await self._authenticate_or_raise(credentials)
        access_token = self.token_service.encode_access_token(subject=user.username)
        return Token(access_token=access_token)

    async def register(self, registration: RegisterUser) -> AuthenticatedUser:
        username = self._normalize_username(registration.username)
        self._validate_password_policy(registration.password, username)

        async with self.unit_of_work:
            if await self.auth_repository.username_exists(username):
                raise ConflictException(
                    message="Username already exists",
                    details={"username": username},
                )

            user = await self.auth_repository.create(
                username=username,
                hashed_password=self.password_service.hash_password(registration.password),
                disabled=False,
            )

        return AuthenticatedUser.model_validate(user)

    def _validate_update_request(self, update_data: UpdateCurrentUser) -> None:
        if update_data.current_password and update_data.new_password is None:
            raise InvalidInputException(message="new_password is required when current_password is provided")

        if update_data.new_password and update_data.current_password is None:
            raise InvalidInputException(message="current_password is required to update password")

        if update_data.username is None and update_data.new_password is None:
            raise InvalidInputException(message="At least one field must be provided to update the user")

    async def _build_username_change(self, current_user: User, username: str | None) -> tuple[str, dict[str, str]]:
        if username is None:
            return current_user.username, {}

        normalized_username = self._normalize_username(username)
        if normalized_username == current_user.username:
            return normalized_username, {}

        if await self.auth_repository.username_exists(
            normalized_username,
            exclude_user_id=current_user.id,
        ):
            raise ConflictException(
                message="Username already exists",
                details={"username": normalized_username},
            )

        return normalized_username, {"username": normalized_username}

    def _build_password_change(
        self,
        current_user: User,
        update_data: UpdateCurrentUser,
        normalized_username: str,
    ) -> dict[str, str]:
        if update_data.new_password is None:
            return {}

        assert update_data.current_password is not None
        if not self.password_service.verify_password(update_data.current_password, current_user.hashed_password):
            raise UnauthorizedException(message="Current password is invalid")

        if self.password_service.verify_password(update_data.new_password, current_user.hashed_password):
            raise InvalidInputException(message="New password must be different from current password")

        self._validate_password_policy(update_data.new_password, normalized_username)
        return {"hashed_password": self.password_service.hash_password(update_data.new_password)}

    async def _persist_user_changes(self, current_user: User, changes: dict[str, str]) -> User:
        return await self.auth_repository.update(current_user, **changes)

    async def update_current_user(self, current_user: User, update_data: UpdateCurrentUser) -> AuthenticatedUser:
        self._validate_update_request(update_data)
        async with self.unit_of_work:
            normalized_username, username_change = await self._build_username_change(current_user, update_data.username)
            password_change = self._build_password_change(current_user, update_data, normalized_username)

            changes = {**username_change, **password_change}
            if not changes:
                raise InvalidInputException(message="No changes detected")

            updated_user = await self._persist_user_changes(current_user, changes)
        return AuthenticatedUser.model_validate(updated_user)

    async def get_user_from_token(self, token: str) -> User:
        payload = self.token_service.decode_access_token(token)
        if payload is None:
            raise UnauthorizedException(message="Could not validate credentials")

        user = await self.auth_repository.get_by_username(payload.sub)
        if user is None:
            raise UnauthorizedException(message="Could not validate credentials")

        return user

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
        granted_scope = await self.auth_repository.get_user_permission_scope(
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
