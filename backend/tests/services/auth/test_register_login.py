import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors.repositories import RepositoryConflictError
from app.core.errors.services import ConflictError, ForbiddenError, UnauthorizedError
from app.features.auth.schemas import LoginCommand, RegisterUserCommand
from utils.testing_support.auth_service import assert_unit_of_work_scope_committed, build_service, build_user


def test_authenticate_or_raise_raises_unauthorized_when_user_not_found() -> None:
    service, repository = build_service()
    credentials = LoginCommand(username="John", password="StrongPass1")
    repository.get_by_username.return_value = None

    async def run_test() -> None:
        with pytest.raises(UnauthorizedError) as exc_info:
            await service._authenticate_or_raise(credentials)

        assert "Invalid username or password" in str(exc_info.value)
        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())


def test_authenticate_or_raise_raises_unauthorized_when_password_is_invalid() -> None:
    service, repository = build_service()
    credentials = LoginCommand(username="john", password="WrongPass1")
    repository.get_by_username.return_value = build_user(service, password="StrongPass1")

    async def run_test() -> None:
        with pytest.raises(UnauthorizedError):
            await service._authenticate_or_raise(credentials)

    asyncio.run(run_test())


def test_authenticate_or_raise_raises_forbidden_for_disabled_user() -> None:
    service, repository = build_service()
    credentials = LoginCommand(username="john", password="StrongPass1")
    repository.get_by_username.return_value = build_user(service, disabled=True)

    async def run_test() -> None:
        with pytest.raises(ForbiddenError) as exc_info:
            await service._authenticate_or_raise(credentials)

        assert "Inactive user" in str(exc_info.value)

    asyncio.run(run_test())


def test_login_returns_bearer_token_for_authenticated_user() -> None:
    service, repository = build_service()
    credentials = LoginCommand(username="john", password="StrongPass1")
    repository.get_by_username.return_value = build_user(service)

    async def run_test() -> None:
        with patch.object(
            service.token_service, "encode_access_token", return_value="encoded-token"
        ) as encode_access_token:
            token = await service.login(credentials)

        assert token.access_token == "encoded-token"
        assert token.token_type == "bearer"
        repository.get_rbac_version.assert_awaited_once_with(1)
        encode_access_token.assert_called_once_with(
            subject="john",
            rbac_version="0" * 64,
        )

    asyncio.run(run_test())


def test_register_raises_conflict_when_username_already_exists() -> None:
    service, repository = build_service()
    repository.username_exists.return_value = True
    registration = RegisterUserCommand(username=" John ", password="StrongPass1")

    async def run_test() -> None:
        with pytest.raises(ConflictError) as exc_info:
            await service.register(registration)

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "john"}
        repository.create_user.assert_not_called()

    asyncio.run(run_test())


def test_register_creates_user_and_returns_authenticated_user() -> None:
    service, repository = build_service()
    registration = RegisterUserCommand(username=" John ", password="StrongPass1")

    async def create_user(**kwargs: str | bool):
        from app.features.auth.models import User

        return User(
            id=42,
            username=str(kwargs["username"]),
            hashed_password=str(kwargs["hashed_password"]),
            disabled=bool(kwargs["disabled"]),
        )

    repository.create_user.side_effect = create_user

    async def run_test() -> None:
        authenticated_user = await service.register(registration)

        assert authenticated_user.id == 42
        assert authenticated_user.username == "john"
        assert authenticated_user.disabled is False
        assert authenticated_user.permissions == ()
        repository.username_exists.assert_awaited_once_with("john")
        repository.create_user.assert_awaited_once()
        assert_unit_of_work_scope_committed(service.unit_of_work)
        created_kwargs = repository.create_user.await_args.kwargs
        assert created_kwargs["username"] == "john"
        assert created_kwargs["disabled"] is False
        assert created_kwargs["hashed_password"] != registration.password
        assert (
            service.password_service.verify_password(registration.password, created_kwargs["hashed_password"]) is True
        )

    asyncio.run(run_test())


def test_register_maps_effective_permissions_into_authenticated_user_result() -> None:
    service, repository = build_service()
    repository.get_user_effective_permission_ids = AsyncMock(
        return_value=("users:manage", "roles:manage", "users:manage")
    )
    registration = RegisterUserCommand(username="john", password="StrongPass1")

    async def create_user(**kwargs: str | bool):
        from app.features.auth.models import User

        return User(
            id=42,
            username=str(kwargs["username"]),
            hashed_password=str(kwargs["hashed_password"]),
            disabled=bool(kwargs["disabled"]),
        )

    repository.create_user.side_effect = create_user

    async def run_test() -> None:
        authenticated_user = await service.register(registration)

        assert authenticated_user.permissions == ("roles:manage", "users:manage")
        repository.get_user_effective_permission_ids.assert_awaited_once_with(42)

    asyncio.run(run_test())


def test_register_propagates_repository_conflict_from_create() -> None:
    service, repository = build_service()
    registration = RegisterUserCommand(username="john", password="StrongPass1")
    repository.create_user.side_effect = RepositoryConflictError(
        message="Username already exists",
        details={"username": "john"},
    )

    async def run_test() -> None:
        with pytest.raises(RepositoryConflictError) as exc_info:
            await service.register(registration)

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "john"}

    asyncio.run(run_test())
