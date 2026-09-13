import logging
from unittest.mock import MagicMock, call, patch

from app.core.common.observability import (
    LOG_COLLECTION_MAX_ITEMS,
    LOG_REDACTION_MAX_DEPTH,
    LOG_VALUE_MAX_LENGTH,
    MAX_DEPTH_LOG_VALUE,
    REDACTED_LOG_VALUE,
    TRUNCATED_LOG_VALUE,
    log_layer_event,
    redact_log_value,
    resolve_request_id,
    sanitize_log_text,
)


def test_resolve_request_id_accepts_only_the_bounded_safe_grammar() -> None:
    valid = "Request_01.safe-id"
    assert resolve_request_id(valid) == valid

    with patch("app.core.common.observability.uuid4") as uuid_factory:
        uuid_factory.return_value.hex = "generated-id"
        for invalid in (None, "", " bad", "bad id", "bad\nsecond-line", "a" * 65, "-leading"):
            assert resolve_request_id(invalid) == "generated-id"

    assert uuid_factory.call_count == 7


def test_sanitize_log_text_escapes_controls_and_bounds_values() -> None:
    assert sanitize_log_text("safe") == "safe"
    assert sanitize_log_text("line\ncarriage\rtab\t\x00") == "line\\x0acarriage\\x0dtab\\x09\\x00"
    assert sanitize_log_text("x" * (LOG_VALUE_MAX_LENGTH + 1)) == ("x" * LOG_VALUE_MAX_LENGTH + TRUNCATED_LOG_VALUE)


def test_redact_log_value_preserves_shape_redacts_recursively_and_bounds_collections() -> None:
    value = {
        "profile": {
            "password": "never-log-this",  # pragma: allowlist secret
            "nested": [{"API-Key": "also-secret", "name": "safe\nname"}],
        },
        "raw": b"bytes\nvalue",
        "tuple": (True, 3, 1.5, None),
        "opaque": object(),
    }

    result = redact_log_value(value)

    assert result["profile"]["password"] == REDACTED_LOG_VALUE
    assert result["profile"]["nested"] == [{"API-Key": REDACTED_LOG_VALUE, "name": "safe\\x0aname"}]
    assert result["raw"] == "bytes\\x0avalue"
    assert result["tuple"] == (True, 3, 1.5, None)
    assert isinstance(result["opaque"], str)

    long_mapping = {f"key-{index}": index for index in range(LOG_COLLECTION_MAX_ITEMS + 1)}
    bounded_mapping = redact_log_value(long_mapping)
    assert bounded_mapping[TRUNCATED_LOG_VALUE] == 1

    long_list = list(range(LOG_COLLECTION_MAX_ITEMS + 1))
    assert redact_log_value(long_list)[-1] == TRUNCATED_LOG_VALUE
    assert redact_log_value(tuple(long_list))[-1] == TRUNCATED_LOG_VALUE


def test_redact_log_value_stops_at_the_configured_depth() -> None:
    value: object = "leaf"
    for _ in range(LOG_REDACTION_MAX_DEPTH):
        value = {"nested": value}

    current = redact_log_value(value)
    for _ in range(LOG_REDACTION_MAX_DEPTH):
        current = current["nested"]
    assert current == MAX_DEPTH_LOG_VALUE


def test_log_layer_event_keeps_event_and_layer_as_code_controlled_fields() -> None:
    logger = MagicMock()

    log_layer_event(
        logger,
        layer="service",
        event="operation_completed",
        level=logging.WARNING,
        password="secret",  # pragma: allowlist secret
        note="two\nlines",
    )
    log_layer_event(logger, layer="service", event="idle")

    assert logger.log.call_args_list == [
        call(
            logging.WARNING,
            "event=%s layer=%s %s",
            "operation_completed",
            "service",
            f"note=two\\x0alines password={REDACTED_LOG_VALUE}",
        ),
        call(logging.INFO, "event=%s layer=%s", "idle", "service"),
    ]
