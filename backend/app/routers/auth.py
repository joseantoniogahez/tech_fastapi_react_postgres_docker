from fastapi import APIRouter

from app.dependencies import AuthCredentialsDependency, AuthServiceDependency, CurrentActiveUserDependency
from app.exceptions import UnauthorizedException
from app.schemas.auth import AuthenticatedUser, Token

router = APIRouter(tags=["auth"])


@router.post("/token")
async def login_for_access_token(
    credentials: AuthCredentialsDependency,
    auth_service: AuthServiceDependency,
) -> Token:
    token = await auth_service.login(credentials)
    if token is None:
        raise UnauthorizedException(message="Invalid username or password")

    return token


@router.get("/users/me")
async def read_current_user(current_user: CurrentActiveUserDependency) -> AuthenticatedUser:
    return AuthenticatedUser.model_validate(current_user)
