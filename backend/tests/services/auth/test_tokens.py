import asyncio
from unittest.mock import patch

import pytest

from app.exceptions.services import UnauthorizedError
from app.schemas.application.auth import AccessTokenPayload
from utils.testing_support.auth_service import build_service, build_user


def test_get_user_from_token_raises_for_invalid_payload() -> None:
    service, repository = build_service()

    async def run_test() -> None:
        with (
            patch.object(service.token_service, "decode_access_token", return_value=None),
            pytest.raises(UnauthorizedError) as exc_info,
        ):
            await service.get_user_from_token("bad-token")

        assert "Could not validate credentials" in str(exc_info.value)
        repository.get_by_username.assert_not_awaited()

    asyncio.run(run_test())


def test_get_user_from_token_raises_when_user_does_not_exist() -> None:
    service, repository = build_service()
    payload = AccessTokenPayload(sub="john", exp=123456789)
    repository.get_by_username.return_value = None

    async def run_test() -> None:
        with (
            patch.object(service.token_service, "decode_access_token", return_value=payload),
            pytest.raises(UnauthorizedError),
        ):
            await service.get_user_from_token("valid-token")

        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())


def test_get_user_from_token_returns_user_when_token_is_valid() -> None:
    service, repository = build_service()
    payload = AccessTokenPayload(sub="john", exp=123456789)
    expected_user = build_user(service, username="john")
    repository.get_by_username.return_value = expected_user

    async def run_test() -> None:
        with patch.object(service.token_service, "decode_access_token", return_value=payload):
            user = await service.get_user_from_token("valid-token")

        assert user is expected_user
        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())
