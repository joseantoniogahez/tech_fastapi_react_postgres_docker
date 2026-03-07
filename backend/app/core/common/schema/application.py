from typing import Any, Self

from pydantic import BaseModel, ConfigDict


class ApplicationSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_api(cls, payload: BaseModel | dict[str, Any]) -> Self:
        if isinstance(payload, BaseModel):
            return cls.model_validate(payload.model_dump())
        return cls.model_validate(payload)

    @classmethod
    def from_domain(cls, payload: Any) -> Self:
        if isinstance(payload, BaseModel):
            return cls.model_validate(payload.model_dump())
        return cls.model_validate(payload)

    @classmethod
    def from_domain_list(cls, payloads: list[Any]) -> list[Self]:
        return [cls.from_domain(payload) for payload in payloads]
