import asyncio
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from sqlalchemy.exc import IntegrityError

from app.const.settings import AuthSettings
from app.exceptions.services import ConflictException, ForbiddenException, InvalidInputException, UnauthorizedException
from app.models.user import User
from app.schemas.auth import Credentials, RegisterUser, TokenPayload, UpdateCurrentUser
from app.services.auth import AuthService


def _assert_unit_of_work_scope_committed(unit_of_work: object) -> None:
    unit_of_work_mock = cast(MagicMock, unit_of_work)
    unit_of_work_enter = cast(AsyncMock, unit_of_work_mock.__aenter__)
    unit_of_work_exit = cast(AsyncMock, unit_of_work_mock.__aexit__)
    unit_of_work_enter.assert_awaited_once_with()
    unit_of_work_exit.assert_awaited_once_with(None, None, None)


def _build_repository_mock() -> MagicMock:
    repository = MagicMock()
    repository.get_by_username = AsyncMock()
    repository.username_exists = AsyncMock(return_value=False)
    repository.create = AsyncMock()
    repository.update = AsyncMock()
    repository.user_has_permission = AsyncMock()
    return repository


def _build_unit_of_work_mock() -> MagicMock:
    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)
    return unit_of_work


def _build_service(repository: MagicMock | None = None) -> tuple[AuthService, MagicMock]:
    repo = repository or _build_repository_mock()
    unit_of_work = _build_unit_of_work_mock()
    settings = AuthSettings(
        JWT_SECRET_KEY="unit-test-secret",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
    )
    return AuthService(auth_repository=repo, unit_of_work=unit_of_work, auth_settings=settings), repo


def _build_user(
    service: AuthService,
    *,
    user_id: int = 1,
    username: str = "john",
    password: str = "StrongPass1",
    disabled: bool = False,
) -> User:
    return User(
        id=user_id,
        username=username,
        hashed_password=service._hash_password(password),
        disabled=disabled,
    )


def test_normalize_username_trims_and_lowercases() -> None:
    service, _ = _build_service()

    normalized = service._normalize_username("  John.Doe-1_2  ")

    assert normalized == "john.doe-1_2"


def test_normalize_username_raises_for_blank_value() -> None:
    service, _ = _build_service()

    with pytest.raises(InvalidInputException) as exc_info:
        service._normalize_username("   ")

    assert "Username is required" in str(exc_info.value)


def test_normalize_username_raises_for_invalid_format() -> None:
    service, _ = _build_service()

    with pytest.raises(InvalidInputException) as exc_info:
        service._normalize_username("john doe")

    assert "Username has invalid format" in str(exc_info.value)


def test_validate_password_policy_raises_with_all_violations() -> None:
    service, _ = _build_service()

    with pytest.raises(InvalidInputException) as exc_info:
        service._validate_password_policy("short", "john")

    details = cast(dict[str, list[str]], exc_info.value.details)
    violations = details["violations"]
    assert "Password must be at least 8 characters long" in violations
    assert "Password must include at least one uppercase letter" in violations
    assert "Password must include at least one number" in violations


def test_validate_password_policy_catches_lowercase_and_username_rules() -> None:
    service, _ = _build_service()

    with pytest.raises(InvalidInputException) as exc_info:
        service._validate_password_policy("JOHN1234", "john")

    details = cast(dict[str, list[str]], exc_info.value.details)
    violations = details["violations"]
    assert "Password must include at least one lowercase letter" in violations
    assert "Password cannot contain the username" in violations


def test_verify_password_returns_false_for_invalid_hash() -> None:
    service, _ = _build_service()

    assert service._verify_password("StrongPass1", "not-a-valid-hash") is False


def test_encode_and_decode_access_token_round_trip() -> None:
    service, _ = _build_service()

    token = service.encode_access_token("john", expires_delta=timedelta(minutes=5))
    payload = service.decode_access_token(token)

    assert payload is not None
    assert payload.sub == "john"
    assert payload.exp > 0


def test_decode_access_token_returns_none_for_payload_validation_error() -> None:
    service, _ = _build_service()
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode({"exp": exp}, service.secret_key, algorithm=service.algorithm)

    payload = service.decode_access_token(token)

    assert payload is None


def test_authenticate_or_raise_raises_unauthorized_when_user_not_found() -> None:
    service, repository = _build_service()
    credentials = Credentials(username="John", password="StrongPass1")
    repository.get_by_username.return_value = None

    async def run_test() -> None:
        with pytest.raises(UnauthorizedException) as exc_info:
            await service._authenticate_or_raise(credentials)

        assert "Invalid username or password" in str(exc_info.value)
        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())


def test_authenticate_or_raise_raises_unauthorized_when_password_is_invalid() -> None:
    service, repository = _build_service()
    credentials = Credentials(username="john", password="WrongPass1")
    repository.get_by_username.return_value = _build_user(service, password="StrongPass1")

    async def run_test() -> None:
        with pytest.raises(UnauthorizedException):
            await service._authenticate_or_raise(credentials)

    asyncio.run(run_test())


def test_authenticate_or_raise_raises_forbidden_for_disabled_user() -> None:
    service, repository = _build_service()
    credentials = Credentials(username="john", password="StrongPass1")
    repository.get_by_username.return_value = _build_user(service, disabled=True)

    async def run_test() -> None:
        with pytest.raises(ForbiddenException) as exc_info:
            await service._authenticate_or_raise(credentials)

        assert "Inactive user" in str(exc_info.value)

    asyncio.run(run_test())


def test_login_returns_bearer_token_for_authenticated_user() -> None:
    service, repository = _build_service()
    credentials = Credentials(username="john", password="StrongPass1")
    repository.get_by_username.return_value = _build_user(service)

    async def run_test() -> None:
        with patch.object(service, "encode_access_token", return_value="encoded-token") as encode_access_token:
            token = await service.login(credentials)

        assert token.access_token == "encoded-token"
        assert token.token_type == "bearer"
        encode_access_token.assert_called_once_with(subject="john")

    asyncio.run(run_test())


def test_register_raises_conflict_when_username_already_exists() -> None:
    service, repository = _build_service()
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
    service, repository = _build_service()
    registration = RegisterUser(username=" John ", password="StrongPass1")

    async def create_user(**kwargs: str | bool) -> User:
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
        _assert_unit_of_work_scope_committed(service.unit_of_work)
        created_kwargs = repository.create.await_args.kwargs
        assert created_kwargs["username"] == "john"
        assert created_kwargs["disabled"] is False
        assert created_kwargs["hashed_password"] != registration.password
        assert service._verify_password(registration.password, created_kwargs["hashed_password"]) is True

    asyncio.run(run_test())


def test_register_raises_conflict_when_create_hits_integrity_error() -> None:
    service, repository = _build_service()
    registration = RegisterUser(username="john", password="StrongPass1")
    repository.create.side_effect = IntegrityError("insert", {}, Exception("duplicate"))

    async def run_test() -> None:
        with pytest.raises(ConflictException) as exc_info:
            await service.register(registration)

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "john"}

    asyncio.run(run_test())


def test_validate_update_request_enforces_required_combinations() -> None:
    service, _ = _build_service()

    with pytest.raises(InvalidInputException) as missing_new_password:
        service._validate_update_request(UpdateCurrentUser(current_password="CurrentPass1"))
    assert "new_password is required" in str(missing_new_password.value)

    with pytest.raises(InvalidInputException) as missing_current_password:
        service._validate_update_request(UpdateCurrentUser(new_password="NewPass123"))
    assert "current_password is required" in str(missing_current_password.value)

    with pytest.raises(InvalidInputException) as empty_update:
        service._validate_update_request(UpdateCurrentUser())
    assert "At least one field must be provided" in str(empty_update.value)


def test_build_username_change_handles_none_and_same_username() -> None:
    service, repository = _build_service()
    current_user = _build_user(service, user_id=7, username="john")

    async def run_test() -> None:
        normalized, changes = await service._build_username_change(current_user, None)
        assert normalized == "john"
        assert changes == {}

        normalized, changes = await service._build_username_change(current_user, "  JOHN ")
        assert normalized == "john"
        assert changes == {}
        repository.username_exists.assert_not_awaited()

    asyncio.run(run_test())


def test_build_username_change_raises_conflict_for_taken_username() -> None:
    service, repository = _build_service()
    current_user = _build_user(service, user_id=8, username="john")
    repository.username_exists.return_value = True

    async def run_test() -> None:
        with pytest.raises(ConflictException) as exc_info:
            await service._build_username_change(current_user, "new-user")

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "new-user"}
        repository.username_exists.assert_awaited_once_with("new-user", exclude_user_id=8)

    asyncio.run(run_test())


def test_build_password_change_validates_current_and_new_password() -> None:
    service, _ = _build_service()
    current_user = _build_user(service, username="john", password="StrongPass1")

    assert service._build_password_change(current_user, UpdateCurrentUser(username="john"), "john") == {}

    with pytest.raises(UnauthorizedException) as invalid_current:
        service._build_password_change(
            current_user,
            UpdateCurrentUser(current_password="WrongPass1", new_password="AnotherPass1"),
            "john",
        )
    assert "Current password is invalid" in str(invalid_current.value)

    with pytest.raises(InvalidInputException) as same_password:
        service._build_password_change(
            current_user,
            UpdateCurrentUser(current_password="StrongPass1", new_password="StrongPass1"),
            "john",
        )
    assert "New password must be different from current password" in str(same_password.value)

    changes = service._build_password_change(
        current_user,
        UpdateCurrentUser(current_password="StrongPass1", new_password="AnotherPass1"),
        "john",
    )
    assert "hashed_password" in changes
    assert service._verify_password("AnotherPass1", changes["hashed_password"]) is True


def test_persist_user_changes_maps_integrity_error_for_username_change() -> None:
    service, repository = _build_service()
    current_user = _build_user(service)
    repository.update.side_effect = IntegrityError("update", {}, Exception("duplicate"))

    async def run_test() -> None:
        with pytest.raises(ConflictException) as exc_info:
            await service._persist_user_changes(current_user, {"username": "new-user"})

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "new-user"}

    asyncio.run(run_test())


def test_persist_user_changes_reraises_non_username_integrity_error() -> None:
    service, repository = _build_service()
    current_user = _build_user(service)
    repository.update.side_effect = IntegrityError("update", {}, Exception("constraint"))

    async def run_test() -> None:
        with pytest.raises(IntegrityError):
            await service._persist_user_changes(current_user, {"hashed_password": "hash"})

    asyncio.run(run_test())


def test_update_current_user_raises_when_no_changes_are_detected() -> None:
    service, _ = _build_service()
    current_user = _build_user(service, username="john")
    update_data = UpdateCurrentUser(username="  JOHN ")

    async def run_test() -> None:
        with pytest.raises(InvalidInputException) as exc_info:
            await service.update_current_user(current_user, update_data)

        assert "No changes detected" in str(exc_info.value)

    asyncio.run(run_test())


def test_update_current_user_persists_username_and_password_changes() -> None:
    service, repository = _build_service()
    current_user = _build_user(service, user_id=9, username="john", password="StrongPass1")
    updated_user = _build_user(service, user_id=9, username="new.user", password="AnotherPass1")
    repository.update.return_value = updated_user
    update_data = UpdateCurrentUser(
        username="new.user",
        current_password="StrongPass1",
        new_password="AnotherPass1",
    )

    async def run_test() -> None:
        result = await service.update_current_user(current_user, update_data)

        assert result.id == 9
        assert result.username == "new.user"
        assert result.disabled is False
        repository.username_exists.assert_awaited_once_with("new.user", exclude_user_id=9)
        repository.update.assert_awaited_once()
        _assert_unit_of_work_scope_committed(service.unit_of_work)
        update_kwargs = repository.update.await_args.kwargs
        assert update_kwargs["username"] == "new.user"
        assert service._verify_password("AnotherPass1", update_kwargs["hashed_password"]) is True

    asyncio.run(run_test())


def test_get_user_from_token_raises_for_invalid_payload() -> None:
    service, repository = _build_service()

    async def run_test() -> None:
        with patch.object(service, "decode_access_token", return_value=None):
            with pytest.raises(UnauthorizedException) as exc_info:
                await service.get_user_from_token("bad-token")

        assert "Could not validate credentials" in str(exc_info.value)
        repository.get_by_username.assert_not_awaited()

    asyncio.run(run_test())


def test_get_user_from_token_raises_when_user_does_not_exist() -> None:
    service, repository = _build_service()
    payload = TokenPayload(sub="john", exp=123456789)
    repository.get_by_username.return_value = None

    async def run_test() -> None:
        with patch.object(service, "decode_access_token", return_value=payload):
            with pytest.raises(UnauthorizedException):
                await service.get_user_from_token("valid-token")

        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())


def test_get_user_from_token_returns_user_when_token_is_valid() -> None:
    service, repository = _build_service()
    payload = TokenPayload(sub="john", exp=123456789)
    expected_user = _build_user(service, username="john")
    repository.get_by_username.return_value = expected_user

    async def run_test() -> None:
        with patch.object(service, "decode_access_token", return_value=payload):
            user = await service.get_user_from_token("valid-token")

        assert user is expected_user
        repository.get_by_username.assert_awaited_once_with("john")

    asyncio.run(run_test())


def test_user_has_permission_delegates_to_repository() -> None:
    service, repository = _build_service()
    repository.user_has_permission.return_value = True

    async def run_test() -> None:
        has_permission = await service.user_has_permission(user_id=1, permission_id="books:create")

        assert has_permission is True
        repository.user_has_permission.assert_awaited_once_with(user_id=1, permission_id="books:create")

    asyncio.run(run_test())
