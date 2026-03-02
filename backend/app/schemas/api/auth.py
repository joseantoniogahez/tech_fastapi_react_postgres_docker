from typing import Literal

from pydantic import ConfigDict, Field

from .base import ApiSchema


class Credentials(ApiSchema):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class Token(ApiSchema):
    access_token: str = Field(min_length=1)
    token_type: Literal["bearer"] = "bearer"


class AuthenticatedUser(ApiSchema):
    id: int
    username: str = Field(min_length=1, max_length=255)
    disabled: bool

    model_config = ConfigDict(from_attributes=True)


class RegisterUser(ApiSchema):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateCurrentUser(ApiSchema):
    username: str | None = Field(default=None, min_length=1, max_length=255)
    current_password: str | None = Field(default=None, min_length=1, max_length=255)
    new_password: str | None = Field(default=None, min_length=8, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)
