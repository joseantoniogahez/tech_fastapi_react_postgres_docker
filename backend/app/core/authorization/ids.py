import re
from typing import Final

PERMISSION_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")


def build_permission_id(*, resource: str, action: str) -> str:
    permission_id = f"{resource}:{action}"
    if PERMISSION_ID_PATTERN.fullmatch(permission_id) is None:
        raise ValueError(
            f"Invalid permission id '{permission_id}'. "
            "Expected '<resource>:<action>' with lowercase letters, numbers, and underscores."
        )
    return permission_id
