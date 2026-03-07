from datetime import datetime
from typing import Any

from pydantic import ConfigDict

from app.core.common.schema import ApplicationSchema


class EnqueueOutboxEventCommand(ApplicationSchema):
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any]


class OutboxEventRecord(ApplicationSchema):
    id: int
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime
    published_at: datetime | None

    model_config = ConfigDict(frozen=True, from_attributes=True)


class OutboxEventResult(OutboxEventRecord):
    pass
