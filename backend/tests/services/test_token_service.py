from datetime import UTC, datetime, timedelta

import jwt

from app.const.settings import AuthSettings
from app.services.token_service import JwtTokenService


def _build_token_service() -> JwtTokenService:
    settings = AuthSettings(
        JWT_SECRET_KEY="unit-test-secret",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
    )
    return JwtTokenService(settings)


def test_encode_and_decode_access_token_round_trip() -> None:
    token_service = _build_token_service()

    token = token_service.encode_access_token("john", expires_delta=timedelta(minutes=5))
    payload = token_service.decode_access_token(token)

    assert payload is not None
    assert payload.sub == "john"
    assert payload.exp > 0


def test_decode_access_token_returns_none_for_payload_validation_error() -> None:
    token_service = _build_token_service()
    exp = datetime.now(UTC) + timedelta(minutes=5)
    token = jwt.encode({"exp": exp}, token_service.secret_key, algorithm=token_service.algorithm)

    payload = token_service.decode_access_token(token)

    assert payload is None
