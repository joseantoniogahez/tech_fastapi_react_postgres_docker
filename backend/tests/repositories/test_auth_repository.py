import asyncio
from unittest.mock import AsyncMock, patch

from app.repositories.auth import AuthRepository
from utils.testing_support.repositories import build_session_mock


def test_auth_repository_user_has_permission_delegates_to_scope_lookup() -> None:
    session = build_session_mock()
    repository = AuthRepository(session=session)

    async def run_test() -> None:
        get_scope_mock = AsyncMock(return_value="any")
        with patch.object(repository, "get_user_permission_scope", get_scope_mock):
            has_permission = await repository.user_has_permission(user_id=3, permission_id="books:update")

        assert has_permission is True
        get_scope_mock.assert_awaited_once_with(
            user_id=3,
            permission_id="books:update",
        )

    asyncio.run(run_test())
