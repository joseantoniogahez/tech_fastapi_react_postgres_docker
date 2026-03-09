from datetime import UTC, datetime, timedelta

import jwt

from app.core.config.settings import AuthSettings
from app.core.security.service import JwtTokenService


def _build_token_service() -> JwtTokenService:
    settings = AuthSettings(
        JWT_SECRET_KEY="unit-test-secret",  # pragma: allowlist secret
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
        JWT_ISSUER="unit-test-issuer",
        JWT_AUDIENCE="unit-test-audience",
    )
    return JwtTokenService(settings)


def test_encode_and_decode_access_token_round_trip() -> None:
    token_service = _build_token_service()

    token = token_service.encode_access_token(
        "john",
        rbac_version="a" * 64,
        expires_delta=timedelta(minutes=5),
    )
    payload = token_service.decode_access_token(token)

    assert payload is not None
    assert payload.sub == "john"
    assert payload.iss == "unit-test-issuer"
    assert payload.aud == "unit-test-audience"
    assert payload.iat > 0
    assert payload.exp > 0
    assert payload.jti
    assert payload.rbac_version == "a" * 64


def test_decode_access_token_returns_none_for_payload_validation_error() -> None:
    token_service = _build_token_service()
    exp = datetime.now(UTC) + timedelta(minutes=5)
    token = jwt.encode({"exp": exp}, token_service.secret_key, algorithm=token_service.algorithm)

    payload = token_service.decode_access_token(token)

    assert payload is None


def test_decode_access_token_returns_none_when_audience_does_not_match() -> None:
    token_service = _build_token_service()
    token = jwt.encode(
        {
            "sub": "john",
            "iss": "unit-test-issuer",
            "aud": "different-audience",
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
            "jti": "token-123",
            "rbac_version": "a" * 64,
        },
        token_service.secret_key,
        algorithm=token_service.algorithm,
    )

    payload = token_service.decode_access_token(token)

    assert payload is None
