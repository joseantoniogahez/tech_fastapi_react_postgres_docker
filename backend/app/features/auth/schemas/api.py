from typing import Literal

from pydantic import ConfigDict, Field

from app.core.common.schema import ApiSchema


class LoginCredentialsRequest(ApiSchema):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class AccessTokenResponse(ApiSchema):
    access_token: str = Field(min_length=1)
    token_type: Literal["bearer"] = "bearer"


class AuthenticatedUserResponse(ApiSchema):
    id: int
    username: str = Field(min_length=1, max_length=255)
    disabled: bool

    model_config = ConfigDict(from_attributes=True)


class RegisterUserRequest(ApiSchema):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateCurrentUserRequest(ApiSchema):
    username: str | None = Field(default=None, min_length=1, max_length=255)
    current_password: str | None = Field(default=None, min_length=1, max_length=255)
    new_password: str | None = Field(default=None, min_length=8, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)
