from typing import Protocol

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


class PasswordServicePort(Protocol):
    def hash_password(self, plain_password: str) -> str: ...

    def verify_password(self, plain_password: str, hashed_password: str) -> bool: ...


class Argon2PasswordService:
    def __init__(self):
        self.password_hasher = PasswordHasher()

    def hash_password(self, plain_password: str) -> str:
        return self.password_hasher.hash(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return self.password_hasher.verify(hashed_password, plain_password)
        except VerifyMismatchError, VerificationError, InvalidHashError:
            return False
