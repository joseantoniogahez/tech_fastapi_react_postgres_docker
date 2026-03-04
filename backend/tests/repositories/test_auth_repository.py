import asyncio
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions.repositories import RepositoryConflictError, RepositoryInternalError
from app.models.user import User
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


def test_auth_repository_get_rbac_version_returns_stable_digest_for_effective_permissions() -> None:
    session = build_session_mock()
    repository = AuthRepository(session=session)
    result = MagicMock()
    result.all.return_value = [
        ("books:update", "own"),
        ("books:update", "any"),
        ("authors:read", "tenant"),
        ("ignored", "invalid"),
    ]
    session.execute.return_value = result

    async def run_test() -> None:
        rbac_version = await repository.get_rbac_version(user_id=7)

        expected = hashlib.sha256(b"authors:read:tenant|books:update:any").hexdigest()
        assert rbac_version == expected
        session.execute.assert_awaited_once()

    asyncio.run(run_test())


def test_auth_repository_create_translates_integrity_error_to_repository_conflict() -> None:
    session = build_session_mock()
    session.flush.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
    repository = AuthRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await repository.create(
                username="john",
                hashed_password="hash",
                disabled=False,
            )

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "john"}
        session.refresh.assert_not_awaited()

    asyncio.run(run_test())


def test_auth_repository_create_translates_non_username_integrity_error_to_repository_internal_error() -> None:
    session = build_session_mock()
    session.flush.side_effect = IntegrityError("insert", {}, Exception("constraint"))
    repository = AuthRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryInternalError) as exc_info:
            await repository.create(
                username=None,
                hashed_password="hash",
                disabled=False,
            )

        assert "Internal server error" in str(exc_info.value)
        session.refresh.assert_not_awaited()

    asyncio.run(run_test())


def test_auth_repository_update_translates_username_integrity_error_to_repository_conflict() -> None:
    session = build_session_mock()
    session.flush.side_effect = IntegrityError("update", {}, Exception("duplicate"))
    user = User(id=3, username="john", hashed_password="hash", disabled=False)
    session.merge.return_value = user
    repository = AuthRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await repository.update(user, username="new-user")

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "new-user"}
        session.refresh.assert_not_awaited()

    asyncio.run(run_test())


def test_auth_repository_update_translates_other_integrity_errors_to_repository_internal_error() -> None:
    session = build_session_mock()
    session.flush.side_effect = IntegrityError("update", {}, Exception("constraint"))
    user = User(id=3, username="john", hashed_password="hash", disabled=False)
    session.merge.return_value = user
    repository = AuthRepository(session=session)

    async def run_test() -> None:
        with pytest.raises(RepositoryInternalError) as exc_info:
            await repository.update(user, hashed_password="new-hash")

        assert "Internal server error" in str(exc_info.value)
        session.refresh.assert_not_awaited()

    asyncio.run(run_test())
