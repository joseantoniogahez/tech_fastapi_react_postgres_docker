import asyncio
from unittest.mock import patch

import pytest

from app.exceptions.repositories import RepositoryConflictException
from app.exceptions.services import ConflictException, ForbiddenException, UnauthorizedException
from app.schemas.auth import Credentials, RegisterUser
from utils.testing_support.auth_service import assert_unit_of_work_scope_committed, build_service, build_user


def test_authenticate_or_raise_raises_unauthorized_when_user_not_found() -> None:
    service, repository = build_service()
    credentials = Credentials(username="John", password="StrongPass1")
    repository.get_by_username.return_value = None

    async def run_test() -> None:
        with pytest.raises(UnauthorizedException) as exc_info:
            await service._authenticate_or_raise(credentials)

        assert "Invalid username or password" in str(exc_info.value)
        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())


def test_authenticate_or_raise_raises_unauthorized_when_password_is_invalid() -> None:
    service, repository = build_service()
    credentials = Credentials(username="john", password="WrongPass1")
    repository.get_by_username.return_value = build_user(service, password="StrongPass1")

    async def run_test() -> None:
        with pytest.raises(UnauthorizedException):
            await service._authenticate_or_raise(credentials)

    asyncio.run(run_test())


def test_authenticate_or_raise_raises_forbidden_for_disabled_user() -> None:
    service, repository = build_service()
    credentials = Credentials(username="john", password="StrongPass1")
    repository.get_by_username.return_value = build_user(service, disabled=True)

    async def run_test() -> None:
        with pytest.raises(ForbiddenException) as exc_info:
            await service._authenticate_or_raise(credentials)

        assert "Inactive user" in str(exc_info.value)

    asyncio.run(run_test())


def test_login_returns_bearer_token_for_authenticated_user() -> None:
    service, repository = build_service()
    credentials = Credentials(username="john", password="StrongPass1")
    repository.get_by_username.return_value = build_user(service)

    async def run_test() -> None:
        with patch.object(
            service.token_service, "encode_access_token", return_value="encoded-token"
        ) as encode_access_token:
            token = await service.login(credentials)

        assert token.access_token == "encoded-token"
        assert token.token_type == "bearer"
        encode_access_token.assert_called_once_with(subject="john")

    asyncio.run(run_test())


def test_register_raises_conflict_when_username_already_exists() -> None:
    service, repository = build_service()
    repository.username_exists.return_value = True
    registration = RegisterUser(username=" John ", password="StrongPass1")

    async def run_test() -> None:
        with pytest.raises(ConflictException) as exc_info:
            await service.register(registration)

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "john"}
        repository.create.assert_not_called()

    asyncio.run(run_test())


def test_register_creates_user_and_returns_authenticated_user() -> None:
    service, repository = build_service()
    registration = RegisterUser(username=" John ", password="StrongPass1")

    async def create_user(**kwargs: str | bool):
        from app.models.user import User

        return User(
            id=42,
            username=str(kwargs["username"]),
            hashed_password=str(kwargs["hashed_password"]),
            disabled=bool(kwargs["disabled"]),
        )

    repository.create.side_effect = create_user

    async def run_test() -> None:
        authenticated_user = await service.register(registration)

        assert authenticated_user.id == 42
        assert authenticated_user.username == "john"
        assert authenticated_user.disabled is False
        repository.username_exists.assert_awaited_once_with("john")
        repository.create.assert_awaited_once()
        assert_unit_of_work_scope_committed(service.unit_of_work)
        created_kwargs = repository.create.await_args.kwargs
        assert created_kwargs["username"] == "john"
        assert created_kwargs["disabled"] is False
        assert created_kwargs["hashed_password"] != registration.password
        assert (
            service.password_service.verify_password(registration.password, created_kwargs["hashed_password"]) is True
        )

    asyncio.run(run_test())


def test_register_propagates_repository_conflict_from_create() -> None:
    service, repository = build_service()
    registration = RegisterUser(username="john", password="StrongPass1")
    repository.create.side_effect = RepositoryConflictException(
        message="Username already exists",
        details={"username": "john"},
    )

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictException) as exc_info:
            await service.register(registration)

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "john"}

    asyncio.run(run_test())
