from typing import Any, Self

from pydantic import BaseModel


class ApiSchema(BaseModel):
    @classmethod
    def from_application(cls, payload: BaseModel | dict[str, Any]) -> Self:
        if isinstance(payload, BaseModel):
            return cls.model_validate(payload.model_dump())
        return cls.model_validate(payload)
