from pydantic import ConfigDict, Field

from .base import ApiSchema


class AuthorBase(ApiSchema):
    name: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class AuthorResponse(AuthorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
