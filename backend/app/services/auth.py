from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jwt import InvalidTokenError
from pydantic import ValidationError

from app.const.settings import AuthSettings
from app.models.user import User
from app.repositories.auth import AuthRepository
from app.schemas.auth import Credentials, Token, TokenPayload
from app.services import Service


class AuthService(Service):
    def __init__(self, auth_repository: AuthRepository, auth_settings: AuthSettings | None = None):
        settings = auth_settings or AuthSettings()
        self.auth_repository = auth_repository
        self.password_hasher = PasswordHasher()
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

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

    async def authenticate(self, credentials: Credentials) -> User | None:
        user = await self.auth_repository.get_by_username(credentials.username)
        if user is None:
            return None

        if not self._verify_password(credentials.password, user.hashed_password):
            return None

        return user

    async def login(self, credentials: Credentials) -> Token | None:
        user = await self.authenticate(credentials)
        if user is None:
            return None

        access_token = self.encode_access_token(subject=user.username)
        return Token(access_token=access_token)

    async def get_user_from_token(self, token: str) -> User | None:
        payload = self.decode_access_token(token)
        if payload is None:
            return None
        return await self.auth_repository.get_by_username(payload.sub)

    async def user_has_permission(self, user_id: int, permission_id: str) -> bool:
        return await self.auth_repository.user_has_permission(user_id=user_id, permission_id=permission_id)
