from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

import jwt
from jwt import InvalidTokenError
from pydantic import ValidationError

from app.core.config.settings import AuthSettings
from app.features.auth.schemas import AccessTokenPayload


class TokenServicePort(Protocol):
    def encode_access_token(
        self,
        subject: str,
        *,
        rbac_version: str,
        expires_delta: timedelta | None = None,
    ) -> str: ...

    def decode_access_token(self, token: str) -> AccessTokenPayload | None: ...


class JwtTokenService:
    def __init__(self, auth_settings: AuthSettings | None = None):
        settings = auth_settings or AuthSettings()
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.issuer = settings.JWT_ISSUER
        self.audience = settings.JWT_AUDIENCE

    def encode_access_token(
        self,
        subject: str,
        *,
        rbac_version: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        expire_delta = expires_delta or timedelta(minutes=self.access_token_expire_minutes)
        issued_at = datetime.now(UTC)
        expire_at = issued_at + expire_delta
        payload = {
            "sub": subject,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": int(issued_at.timestamp()),
            "exp": int(expire_at.timestamp()),
            "jti": uuid4().hex,
            "rbac_version": rbac_version,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> AccessTokenPayload | None:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
            )
            return AccessTokenPayload.model_validate(payload)
        except (InvalidTokenError, ValidationError):
            return None
