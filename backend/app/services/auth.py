import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.repositories.user import UserRepository
from app.schemas.auth import Credentials
from app.services import Service


class AuthService(Service):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.password_hasher = PasswordHasher()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.password_hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    async def authenticate(self, credentials: Credentials) -> str | None:
        user = await self.user_repository.get_by_username(credentials.username)
        if user is None:
            return None

        if not self._verify_password(credentials.password, user.hashed_password):
            return None

        return secrets.token_urlsafe(32)
