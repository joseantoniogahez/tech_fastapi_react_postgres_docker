from pydantic import ConfigDict, Field

from app.core.common.schema import ApplicationSchema


class LoginCommand(ApplicationSchema):
    username: str
    password: str


class RegisterUserCommand(ApplicationSchema):
    username: str
    password: str


class UpdateCurrentUserCommand(ApplicationSchema):
    username: str | None = None
    current_password: str | None = None
    new_password: str | None = None


class AccessTokenResult(ApplicationSchema):
    access_token: str
    token_type: str = "bearer"


class AuthenticatedUserResult(ApplicationSchema):
    id: int
    username: str
    disabled: bool
    permissions: tuple[str, ...] = Field(default_factory=tuple)

    model_config = ConfigDict(frozen=True, from_attributes=True)


class AccessTokenPayload(ApplicationSchema):
    sub: str = Field(min_length=1, max_length=255)
    iss: str = Field(min_length=1, max_length=255)
    aud: str = Field(min_length=1, max_length=255)
    iat: int
    exp: int
    jti: str = Field(min_length=1, max_length=255)
    rbac_version: str = Field(min_length=64, max_length=64)
