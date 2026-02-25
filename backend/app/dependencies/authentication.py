from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.exceptions.services import ForbiddenException
from app.models.user import User
from app.schemas.auth import Credentials

from .services import AuthServiceDependency

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
BearerTokenDependency = Annotated[str, Depends(oauth2_scheme)]


async def get_auth_credentials(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Credentials:
    return Credentials(username=form_data.username, password=form_data.password)


AuthCredentialsDependency = Annotated[Credentials, Depends(get_auth_credentials)]


async def get_current_user(
    token: BearerTokenDependency,
    auth_service: AuthServiceDependency,
) -> User:
    return await auth_service.get_user_from_token(token)


CurrentUserDependency = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUserDependency) -> User:
    if current_user.disabled:
        raise ForbiddenException(message="Inactive user")
    return current_user


CurrentActiveUserDependency = Annotated[User, Depends(get_current_active_user)]
