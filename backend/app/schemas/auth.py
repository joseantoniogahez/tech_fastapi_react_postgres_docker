from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)


class Token(BaseModel):
    access_token: str = Field(min_length=1)
    token_type: Literal["bearer"] = "bearer"


class TokenPayload(BaseModel):
    sub: str = Field(min_length=1, max_length=255)
    exp: int


class AuthenticatedUser(BaseModel):
    id: int
    username: str = Field(min_length=1, max_length=255)
    disabled: bool

    model_config = ConfigDict(from_attributes=True)
