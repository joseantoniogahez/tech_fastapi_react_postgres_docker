from datetime import datetime, timedelta, timezone
from typing import Protocol

import jwt
from jwt import InvalidTokenError
from pydantic import ValidationError

from app.const.settings import AuthSettings
from app.schemas.auth import TokenPayload


class TokenServicePort(Protocol):
    def encode_access_token(self, subject: str, expires_delta: timedelta | None = None) -> str: ...

    def decode_access_token(self, token: str) -> TokenPayload | None: ...


class JwtTokenService:
    def __init__(self, auth_settings: AuthSettings | None = None):
        settings = auth_settings or AuthSettings()
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

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
