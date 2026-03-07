from collections.abc import Callable
from typing import Any, Protocol

from app.core.common.records import UserRecord
from app.core.db.ports import UnitOfWorkPort
from app.core.errors.services import ConflictError, InvalidInputError, UnauthorizedError
from app.core.security.service import PasswordServicePort
from app.features.auth.schemas import UpdateCurrentUserCommand

NormalizeUsername = Callable[[str], str]
ValidatePasswordPolicy = Callable[[str, str], None]


class AuthProfileRepositoryPort(Protocol):
    async def username_exists(self, username: str, *, exclude_user_id: int | None = None) -> bool: ...

    async def update_user(self, user_id: int, **changes: Any) -> UserRecord: ...


class AuthProfileUpdates:
    def __init__(
        self,
        *,
        auth_repository: AuthProfileRepositoryPort,
        unit_of_work: UnitOfWorkPort,
        password_service: PasswordServicePort,
        normalize_username: NormalizeUsername,
        validate_password_policy: ValidatePasswordPolicy,
    ):
        self._auth_repository = auth_repository
        self._unit_of_work = unit_of_work
        self._password_service = password_service
        self._normalize_username = normalize_username
        self._validate_password_policy = validate_password_policy

    def validate_update_request(self, update_data: UpdateCurrentUserCommand) -> None:
        if update_data.current_password and update_data.new_password is None:
            raise InvalidInputError(message="new_password is required when current_password is provided")

        if update_data.new_password and update_data.current_password is None:
            raise InvalidInputError(message="current_password is required to update password")

        if update_data.username is None and update_data.new_password is None:
            raise InvalidInputError(message="At least one field must be provided to update the user")

    async def build_username_change(self, current_user: UserRecord, username: str | None) -> tuple[str, dict[str, str]]:
        if username is None:
            return current_user.username, {}

        normalized_username = self._normalize_username(username)
        if normalized_username == current_user.username:
            return normalized_username, {}

        if await self._auth_repository.username_exists(
            normalized_username,
            exclude_user_id=current_user.id,
        ):
            raise ConflictError(
                message="Username already exists",
                details={"username": normalized_username},
            )

        return normalized_username, {"username": normalized_username}

    def build_password_change(
        self,
        current_user: UserRecord,
        update_data: UpdateCurrentUserCommand,
        normalized_username: str,
    ) -> dict[str, str]:
        if update_data.new_password is None:
            return {}

        assert update_data.current_password is not None
        if not self._password_service.verify_password(update_data.current_password, current_user.hashed_password):
            raise UnauthorizedError(message="Current password is invalid")

        if self._password_service.verify_password(update_data.new_password, current_user.hashed_password):
            raise InvalidInputError(message="New password must be different from current password")

        self._validate_password_policy(update_data.new_password, normalized_username)
        return {"hashed_password": self._password_service.hash_password(update_data.new_password)}

    async def persist_user_changes(self, current_user: UserRecord, changes: dict[str, str]) -> UserRecord:
        return await self._auth_repository.update_user(current_user.id, **changes)

    async def update_current_user(self, current_user: UserRecord, update_data: UpdateCurrentUserCommand) -> UserRecord:
        self.validate_update_request(update_data)
        async with self._unit_of_work:
            normalized_username, username_change = await self.build_username_change(current_user, update_data.username)
            password_change = self.build_password_change(current_user, update_data, normalized_username)

            changes = {**username_change, **password_change}
            if not changes:
                raise InvalidInputError(message="No changes detected")

            return await self.persist_user_changes(current_user, changes)
