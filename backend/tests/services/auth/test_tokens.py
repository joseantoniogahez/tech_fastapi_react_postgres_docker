import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from app.exceptions.services import UnauthorizedException
from app.schemas.auth import TokenPayload
from utils.testing_support.auth_service import build_service, build_user


def test_encode_and_decode_access_token_round_trip() -> None:
    service, _ = build_service()

    token = service.encode_access_token("john", expires_delta=timedelta(minutes=5))
    payload = service.decode_access_token(token)

    assert payload is not None
    assert payload.sub == "john"
    assert payload.exp > 0


def test_decode_access_token_returns_none_for_payload_validation_error() -> None:
    service, _ = build_service()
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode({"exp": exp}, service.secret_key, algorithm=service.algorithm)

    payload = service.decode_access_token(token)

    assert payload is None


def test_get_user_from_token_raises_for_invalid_payload() -> None:
    service, repository = build_service()

    async def run_test() -> None:
        with patch.object(service, "decode_access_token", return_value=None):
            with pytest.raises(UnauthorizedException) as exc_info:
                await service.get_user_from_token("bad-token")

        assert "Could not validate credentials" in str(exc_info.value)
        repository.get_by_username.assert_not_awaited()

    asyncio.run(run_test())


def test_get_user_from_token_raises_when_user_does_not_exist() -> None:
    service, repository = build_service()
    payload = TokenPayload(sub="john", exp=123456789)
    repository.get_by_username.return_value = None

    async def run_test() -> None:
        with patch.object(service, "decode_access_token", return_value=payload):
            with pytest.raises(UnauthorizedException):
                await service.get_user_from_token("valid-token")

        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())


def test_get_user_from_token_returns_user_when_token_is_valid() -> None:
    service, repository = build_service()
    payload = TokenPayload(sub="john", exp=123456789)
    expected_user = build_user(service, username="john")
    repository.get_by_username.return_value = expected_user

    async def run_test() -> None:
        with patch.object(service, "decode_access_token", return_value=payload):
            user = await service.get_user_from_token("valid-token")

        assert user is expected_user
        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())
