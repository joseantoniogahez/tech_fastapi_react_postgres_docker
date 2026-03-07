from typing import cast

import pytest

from app.core.errors.services import InvalidInputError
from utils.testing_support.auth_service import build_service


def test_normalize_username_trims_and_lowercases() -> None:
    service, _ = build_service()

    normalized = service._normalize_username("  John.Doe-1_2  ")

    assert normalized == "john.doe-1_2"


def test_normalize_username_raises_for_blank_value() -> None:
    service, _ = build_service()

    with pytest.raises(InvalidInputError) as exc_info:
        service._normalize_username("   ")

    assert "Username is required" in str(exc_info.value)


def test_normalize_username_raises_for_invalid_format() -> None:
    service, _ = build_service()

    with pytest.raises(InvalidInputError) as exc_info:
        service._normalize_username("john doe")

    assert "Username has invalid format" in str(exc_info.value)


def test_validate_password_policy_raises_with_all_violations() -> None:
    service, _ = build_service()

    with pytest.raises(InvalidInputError) as exc_info:
        service._validate_password_policy("short", "john")

    details = cast(dict[str, list[str]], exc_info.value.details)
    violations = details["violations"]
    assert "Password must be at least 8 characters long" in violations
    assert "Password must include at least one uppercase letter" in violations
    assert "Password must include at least one number" in violations


def test_validate_password_policy_catches_lowercase_and_username_rules() -> None:
    service, _ = build_service()

    with pytest.raises(InvalidInputError) as exc_info:
        service._validate_password_policy("JOHN1234", "john")

    details = cast(dict[str, list[str]], exc_info.value.details)
    violations = details["violations"]
    assert "Password must include at least one lowercase letter" in violations
    assert "Password cannot contain the username" in violations
