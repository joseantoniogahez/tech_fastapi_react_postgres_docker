import pytest

from app.security.policies import (
    PasswordPolicyError,
    PasswordPolicyRule,
    UsernamePolicyError,
    UsernamePolicyErrorCode,
    format_password_policy_messages,
    format_password_policy_summary,
    normalize_username,
    validate_password_policy,
)


def test_normalize_username_trims_and_lowercases() -> None:
    assert normalize_username("  John.Doe-1_2  ") == "john.doe-1_2"


def test_normalize_username_raises_code_for_blank_value() -> None:
    with pytest.raises(UsernamePolicyError) as exc_info:
        normalize_username("   ")

    assert exc_info.value.code is UsernamePolicyErrorCode.REQUIRED


def test_normalize_username_raises_code_for_invalid_format() -> None:
    with pytest.raises(UsernamePolicyError) as exc_info:
        normalize_username("john doe")

    assert exc_info.value.code is UsernamePolicyErrorCode.INVALID_FORMAT


def test_validate_password_policy_returns_expected_violation_order_and_messages() -> None:
    with pytest.raises(PasswordPolicyError) as exc_info:
        validate_password_policy("short", "john")

    assert exc_info.value.violations == (
        PasswordPolicyRule.MIN_LENGTH,
        PasswordPolicyRule.UPPERCASE,
        PasswordPolicyRule.NUMBER,
    )
    assert format_password_policy_messages(exc_info.value.violations) == [
        "Password must be at least 8 characters long",
        "Password must include at least one uppercase letter",
        "Password must include at least one number",
    ]
    assert format_password_policy_summary(exc_info.value.violations) == (
        "at least 8 characters, at least one uppercase letter, at least one number"
    )


def test_validate_password_policy_catches_lowercase_and_username_rules() -> None:
    with pytest.raises(PasswordPolicyError) as exc_info:
        validate_password_policy("JOHN1234", "john")

    assert exc_info.value.violations == (
        PasswordPolicyRule.LOWERCASE,
        PasswordPolicyRule.CONTAINS_USERNAME,
    )
