from datetime import datetime

from pydantic import ConfigDict, Field

from app.core.common.schema import ApplicationSchema


class AuditLogEntryResult(ApplicationSchema):
    id: int
    actor_user_id: int | None = None
    action: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str | None = Field(default=None, max_length=100)
    summary: str = Field(min_length=1, max_length=255)
    created_at: datetime

    model_config = ConfigDict(frozen=True, from_attributes=True)
