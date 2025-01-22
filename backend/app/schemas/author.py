from pydantic import BaseModel, ConfigDict, Field


class AuthorBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class Author(AuthorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
