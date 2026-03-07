import logging
from typing import Any


def log_layer_event(
    logger: logging.Logger,
    *,
    layer: str,
    event: str,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    if fields:
        extra = " ".join(f"{key}={fields[key]}" for key in sorted(fields))
        logger.log(level, "event=%s layer=%s %s", event, layer, extra)
        return

    logger.log(level, "event=%s layer=%s", event, layer)
