import logging
import re
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

REQUEST_ID_MAX_LENGTH = 64
LOG_VALUE_MAX_LENGTH = 256
LOG_COLLECTION_MAX_ITEMS = 50
LOG_REDACTION_MAX_DEPTH = 6
REDACTED_LOG_VALUE = "[REDACTED]"
TRUNCATED_LOG_VALUE = "[TRUNCATED]"
MAX_DEPTH_LOG_VALUE = "[MAX_DEPTH]"

_REQUEST_ID_PATTERN = re.compile(rf"^[A-Za-z0-9][A-Za-z0-9._-]{{0,{REQUEST_ID_MAX_LENGTH - 1}}}$")
_SENSITIVE_KEY_NAMES = {
    "apikey",
    "authorization",
    "clientsecret",
    "cookie",
    "password",
    "passwd",
    "refreshtoken",
    "secret",
    "setcookie",
    "token",
    "accesstoken",
}


def resolve_request_id(candidate: str | None) -> str:
    if candidate is not None and _REQUEST_ID_PATTERN.fullmatch(candidate) is not None:
        return candidate
    return uuid4().hex


def sanitize_log_text(value: str, *, max_length: int = LOG_VALUE_MAX_LENGTH) -> str:
    bounded = value[:max_length]
    escaped = "".join(
        character if character.isprintable() and character not in {"\r", "\n", "\t"} else f"\\x{ord(character):02x}"
        for character in bounded
    )
    if len(value) > max_length:
        return f"{escaped}{TRUNCATED_LOG_VALUE}"
    return escaped


def _is_sensitive_key(key: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    return normalized in _SENSITIVE_KEY_NAMES


def _redact_log_mapping(value: Mapping[Any, Any], *, depth: int) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    items = list(value.items())
    for key, nested_value in items[:LOG_COLLECTION_MAX_ITEMS]:
        safe_key = sanitize_log_text(str(key))
        redacted[safe_key] = (
            REDACTED_LOG_VALUE if _is_sensitive_key(key) else redact_log_value(nested_value, _depth=depth + 1)
        )
    if len(items) > LOG_COLLECTION_MAX_ITEMS:
        redacted[TRUNCATED_LOG_VALUE] = len(items) - LOG_COLLECTION_MAX_ITEMS
    return redacted


def _redact_log_sequence(value: list[Any] | tuple[Any, ...], *, depth: int) -> list[Any] | tuple[Any, ...]:
    redacted = [redact_log_value(item, _depth=depth + 1) for item in value[:LOG_COLLECTION_MAX_ITEMS]]
    if len(value) > LOG_COLLECTION_MAX_ITEMS:
        redacted.append(TRUNCATED_LOG_VALUE)
    return tuple(redacted) if isinstance(value, tuple) else redacted


def redact_log_value(value: Any, *, _depth: int = 0) -> Any:
    if _depth >= LOG_REDACTION_MAX_DEPTH:
        return MAX_DEPTH_LOG_VALUE
    if isinstance(value, str):
        return sanitize_log_text(value)
    if isinstance(value, bytes):
        return sanitize_log_text(value.decode("utf-8", errors="replace"))
    if isinstance(value, Mapping):
        return _redact_log_mapping(value, depth=_depth)
    if isinstance(value, list | tuple):
        return _redact_log_sequence(value, depth=_depth)
    if value is None or isinstance(value, bool | int | float):
        return value
    return sanitize_log_text(str(value))


def log_layer_event(
    logger: logging.Logger,
    *,
    layer: str,
    event: str,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    if fields:
        extra = " ".join(
            f"{sanitize_log_text(key)}="
            f"{REDACTED_LOG_VALUE if _is_sensitive_key(key) else redact_log_value(fields[key])}"
            for key in sorted(fields)
        )
        logger.log(level, "event=%s layer=%s %s", event, layer, extra)
        return

    logger.log(level, "event=%s layer=%s", event, layer)
