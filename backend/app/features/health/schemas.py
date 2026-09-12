from enum import StrEnum

from pydantic import BaseModel


class ReadinessStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"


class ReadinessCheckResponse(BaseModel):
    name: str
    status: ReadinessStatus


class ReadinessResponse(BaseModel):
    status: ReadinessStatus
    checks: list[ReadinessCheckResponse]
