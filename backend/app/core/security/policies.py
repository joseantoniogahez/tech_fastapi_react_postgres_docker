import re
from enum import StrEnum

USERNAME_ALLOWED_DESCRIPTION = "lowercase letters, numbers, dot, underscore and hyphen"


class UsernamePolicyErrorCode(StrEnum):
    REQUIRED = "required"
    INVALID_FORMAT = "invalid_format"


class PasswordPolicyRule(StrEnum):
    MIN_LENGTH = "min_length"
    LOWERCASE = "lowercase"
    UPPERCASE = "uppercase"
    NUMBER = "number"
    CONTAINS_USERNAME = "contains_username"


PASSWORD_POLICY_DETAIL_MESSAGES: dict[PasswordPolicyRule, str] = {
    PasswordPolicyRule.MIN_LENGTH: "Password must be at least 8 characters long",
    PasswordPolicyRule.LOWERCASE: "Password must include at least one lowercase letter",
    PasswordPolicyRule.UPPERCASE: "Password must include at least one uppercase letter",
    PasswordPolicyRule.NUMBER: "Password must include at least one number",
    PasswordPolicyRule.CONTAINS_USERNAME: "Password cannot contain the username",
}

PASSWORD_POLICY_SUMMARY_MESSAGES: dict[PasswordPolicyRule, str] = {
    PasswordPolicyRule.MIN_LENGTH: "at least 8 characters",
    PasswordPolicyRule.LOWERCASE: "at least one lowercase letter",
    PasswordPolicyRule.UPPERCASE: "at least one uppercase letter",
    PasswordPolicyRule.NUMBER: "at least one number",
    PasswordPolicyRule.CONTAINS_USERNAME: "must not contain the username",
}

_USERNAME_PATTERN = re.compile(r"^[a-z0-9_.-]+$")


class UsernamePolicyError(ValueError):
    def __init__(self, code: UsernamePolicyErrorCode):
        self.code = code
        super().__init__(code.value)


class PasswordPolicyError(ValueError):
    def __init__(self, violations: tuple[PasswordPolicyRule, ...]):
        self.violations = violations
        super().__init__("Password does not meet policy")


def normalize_username(username: str) -> str:
    normalized_username = username.strip().lower()
    if not normalized_username:
        raise UsernamePolicyError(UsernamePolicyErrorCode.REQUIRED)

    if _USERNAME_PATTERN.fullmatch(normalized_username) is None:
        raise UsernamePolicyError(UsernamePolicyErrorCode.INVALID_FORMAT)

    return normalized_username


def _collect_password_policy_violations(password: str, username: str) -> tuple[PasswordPolicyRule, ...]:
    violations: list[PasswordPolicyRule] = []
    if len(password) < 8:
        violations.append(PasswordPolicyRule.MIN_LENGTH)
    if re.search(r"[a-z]", password) is None:
        violations.append(PasswordPolicyRule.LOWERCASE)
    if re.search(r"[A-Z]", password) is None:
        violations.append(PasswordPolicyRule.UPPERCASE)
    if re.search(r"\d", password) is None:
        violations.append(PasswordPolicyRule.NUMBER)

    normalized_username = username.strip().lower()
    if normalized_username and normalized_username in password.lower():
        violations.append(PasswordPolicyRule.CONTAINS_USERNAME)

    return tuple(violations)


def validate_password_policy(password: str, username: str) -> None:
    violations = _collect_password_policy_violations(password, username)
    if violations:
        raise PasswordPolicyError(violations)


def format_password_policy_messages(violations: tuple[PasswordPolicyRule, ...]) -> list[str]:
    return [PASSWORD_POLICY_DETAIL_MESSAGES[violation] for violation in violations]


def format_password_policy_summary(violations: tuple[PasswordPolicyRule, ...]) -> str:
    return ", ".join(PASSWORD_POLICY_SUMMARY_MESSAGES[violation] for violation in violations)
