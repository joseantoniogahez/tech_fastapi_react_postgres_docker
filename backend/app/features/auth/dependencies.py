from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.errors.services import ForbiddenError
from app.core.setup.dependencies import AuthServiceDependency
from app.features.auth.principal import CurrentPrincipal
from app.features.auth.schemas import LoginCredentialsRequest

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/token")
BearerTokenDependency = Annotated[str, Depends(oauth2_scheme)]


async def get_auth_credentials(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> LoginCredentialsRequest:
    return LoginCredentialsRequest(username=form_data.username, password=form_data.password)


AuthCredentialsDependency = Annotated[LoginCredentialsRequest, Depends(get_auth_credentials)]


async def get_current_user(
    token: BearerTokenDependency,
    auth_service: AuthServiceDependency,
) -> CurrentPrincipal:
    return await auth_service.get_user_from_token(token)


CurrentUserDependency = Annotated[CurrentPrincipal, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUserDependency) -> CurrentPrincipal:
    if current_user.disabled:
        raise ForbiddenError(message="Inactive user")
    return current_user


CurrentActiveUserDependency = Annotated[CurrentPrincipal, Depends(get_current_active_user)]
