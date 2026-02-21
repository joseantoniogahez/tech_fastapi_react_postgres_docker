from typing import Literal

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)


class Token(BaseModel):
    access_token: str = Field(min_length=1)
    token_type: Literal["bearer"] = "bearer"
