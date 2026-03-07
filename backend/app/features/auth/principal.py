from pydantic import ConfigDict

from app.core.common.schema import ApplicationSchema


class CurrentPrincipal(ApplicationSchema):
    id: int
    username: str
    disabled: bool
    tenant_id: int | None = None

    model_config = ConfigDict(frozen=True, from_attributes=True)
