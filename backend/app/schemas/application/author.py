from pydantic import ConfigDict

from .base import ApplicationSchema


class AuthorResult(ApplicationSchema):
    id: int
    name: str

    model_config = ConfigDict(frozen=True, from_attributes=True)
