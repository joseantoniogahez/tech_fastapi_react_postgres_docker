import re
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jwt import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.const.settings import AuthSettings
from app.exceptions import ConflictException, ForbiddenException, InvalidInputException, UnauthorizedException
from app.models.user import User
from app.repositories.auth import AuthRepository
from app.schemas.auth import AuthenticatedUser, Credentials, RegisterUser, Token, TokenPayload, UpdateCurrentUser
from app.services import Service


class AuthService(Service):
    _username_pattern = re.compile(r"^[a-z0-9_.-]+$")

    def __init__(self, auth_repository: AuthRepository, auth_settings: AuthSettings | None = None):
        settings = auth_settings or AuthSettings()
        self.auth_repository = auth_repository
        self.password_hasher = PasswordHasher()
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    def _normalize_username(self, username: str) -> str:
        normalized_username = username.strip().lower()
        if not normalized_username:
            raise InvalidInputException(message="Username is required")

        if not self._username_pattern.fullmatch(normalized_username):
            raise InvalidInputException(
                message="Username has invalid format",
                details={
                    "allowed": "lowercase letters, numbers, dot, underscore and hyphen",
                },
            )

        return normalized_username

    def _validate_password_policy(self, password: str, username: str) -> None:
        violations: list[str] = []
        if len(password) < 8:
            violations.append("Password must be at least 8 characters long")
        if not re.search(r"[a-z]", password):
            violations.append("Password must include at least one lowercase letter")
        if not re.search(r"[A-Z]", password):
            violations.append("Password must include at least one uppercase letter")
        if not re.search(r"\d", password):
            violations.append("Password must include at least one number")
        if username in password.lower():
            violations.append("Password cannot contain the username")

        if violations:
            raise InvalidInputException(
                message="Password does not meet policy",
                details={"violations": violations},
            )

    def _hash_password(self, plain_password: str) -> str:
        return self.password_hasher.hash(plain_password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.password_hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def encode_access_token(self, subject: str, expires_delta: timedelta | None = None) -> str:
        expire_delta = expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        expire_at = datetime.now(timezone.utc) + expire_delta
        payload = {"sub": subject, "exp": expire_at}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> TokenPayload | None:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenPayload.model_validate(payload)
        except (InvalidTokenError, ValidationError):
            return None

    async def _authenticate_or_raise(self, credentials: Credentials) -> User:
        username = self._normalize_username(credentials.username)
        user = await self.auth_repository.get_by_username(username)
        if user is None or not self._verify_password(credentials.password, user.hashed_password):
            raise UnauthorizedException(message="Invalid username or password")

        if user.disabled:
            raise ForbiddenException(message="Inactive user")

        return user

    async def login(self, credentials: Credentials) -> Token:
        user = await self._authenticate_or_raise(credentials)
        access_token = self.encode_access_token(subject=user.username)
        return Token(access_token=access_token)

    async def register(self, registration: RegisterUser) -> AuthenticatedUser:
        username = self._normalize_username(registration.username)
        self._validate_password_policy(registration.password, username)

        if await self.auth_repository.username_exists(username):
            raise ConflictException(
                message="Username already exists",
                details={"username": username},
            )

        try:
            user = await self.auth_repository.create(
                username=username,
                hashed_password=self._hash_password(registration.password),
                disabled=False,
            )
        except IntegrityError as exc:
            raise ConflictException(
                message="Username already exists",
                details={"username": username},
            ) from exc

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
        if not self._verify_password(update_data.current_password, current_user.hashed_password):
            raise UnauthorizedException(message="Current password is invalid")

        if self._verify_password(update_data.new_password, current_user.hashed_password):
            raise InvalidInputException(message="New password must be different from current password")

        self._validate_password_policy(update_data.new_password, normalized_username)
        return {"hashed_password": self._hash_password(update_data.new_password)}

    async def _persist_user_changes(self, current_user: User, changes: dict[str, str]) -> User:
        try:
            return await self.auth_repository.update(current_user, **changes)
        except IntegrityError as exc:
            if "username" in changes:
                raise ConflictException(
                    message="Username already exists",
                    details={"username": changes["username"]},
                ) from exc
            raise

    async def update_current_user(self, current_user: User, update_data: UpdateCurrentUser) -> AuthenticatedUser:
        self._validate_update_request(update_data)
        normalized_username, username_change = await self._build_username_change(current_user, update_data.username)
        password_change = self._build_password_change(current_user, update_data, normalized_username)

        changes = {**username_change, **password_change}
        if not changes:
            raise InvalidInputException(message="No changes detected")

        updated_user = await self._persist_user_changes(current_user, changes)
        return AuthenticatedUser.model_validate(updated_user)

    async def get_user_from_token(self, token: str) -> User:
        payload = self.decode_access_token(token)
        if payload is None:
            raise UnauthorizedException(message="Could not validate credentials")

        user = await self.auth_repository.get_by_username(payload.sub)
        if user is None:
            raise UnauthorizedException(message="Could not validate credentials")

        return user

    async def user_has_permission(self, user_id: int, permission_id: str) -> bool:
        return await self.auth_repository.user_has_permission(user_id=user_id, permission_id=permission_id)
