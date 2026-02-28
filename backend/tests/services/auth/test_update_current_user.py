import asyncio

import pytest
from sqlalchemy.exc import IntegrityError

from app.exceptions.services import ConflictException, InvalidInputException, UnauthorizedException
from app.schemas.auth import UpdateCurrentUser
from utils.testing_support.auth_service import assert_unit_of_work_scope_committed, build_service, build_user


def test_validate_update_request_enforces_required_combinations() -> None:
    service, _ = build_service()

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
    service, repository = build_service()
    current_user = build_user(service, user_id=7, username="john")

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
    service, repository = build_service()
    current_user = build_user(service, user_id=8, username="john")
    repository.username_exists.return_value = True

    async def run_test() -> None:
        with pytest.raises(ConflictException) as exc_info:
            await service._build_username_change(current_user, "new-user")

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "new-user"}
        repository.username_exists.assert_awaited_once_with("new-user", exclude_user_id=8)

    asyncio.run(run_test())


def test_build_password_change_validates_current_and_new_password() -> None:
    service, _ = build_service()
    current_user = build_user(service, username="john", password="StrongPass1")

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
    service, repository = build_service()
    current_user = build_user(service)
    repository.update.side_effect = IntegrityError("update", {}, Exception("duplicate"))

    async def run_test() -> None:
        with pytest.raises(ConflictException) as exc_info:
            await service._persist_user_changes(current_user, {"username": "new-user"})

        assert "Username already exists" in str(exc_info.value)
        assert exc_info.value.details == {"username": "new-user"}

    asyncio.run(run_test())


def test_persist_user_changes_reraises_non_username_integrity_error() -> None:
    service, repository = build_service()
    current_user = build_user(service)
    repository.update.side_effect = IntegrityError("update", {}, Exception("constraint"))

    async def run_test() -> None:
        with pytest.raises(IntegrityError):
            await service._persist_user_changes(current_user, {"hashed_password": "hash"})

    asyncio.run(run_test())


def test_update_current_user_raises_when_no_changes_are_detected() -> None:
    service, _ = build_service()
    current_user = build_user(service, username="john")
    update_data = UpdateCurrentUser(username="  JOHN ")

    async def run_test() -> None:
        with pytest.raises(InvalidInputException) as exc_info:
            await service.update_current_user(current_user, update_data)

        assert "No changes detected" in str(exc_info.value)

    asyncio.run(run_test())


def test_update_current_user_persists_username_and_password_changes() -> None:
    service, repository = build_service()
    current_user = build_user(service, user_id=9, username="john", password="StrongPass1")
    updated_user = build_user(service, user_id=9, username="new.user", password="AnotherPass1")
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
        assert_unit_of_work_scope_committed(service.unit_of_work)
        update_kwargs = repository.update.await_args.kwargs
        assert update_kwargs["username"] == "new.user"
        assert service._verify_password("AnotherPass1", update_kwargs["hashed_password"]) is True

    asyncio.run(run_test())
