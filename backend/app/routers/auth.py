from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import AuthServiceDependency, CurrentActiveUserDependency
from app.schemas.auth import AuthenticatedUser, Token

router = APIRouter(tags=["auth"])

INVALID_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=401,
    detail="Invalid username or password",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDependency,
) -> Token:
    token = await auth_service.login(form_data.username, form_data.password)
    if token is None:
        raise INVALID_CREDENTIALS_EXCEPTION

    return token


@router.get("/users/me")
async def read_current_user(current_user: CurrentActiveUserDependency) -> AuthenticatedUser:
    return AuthenticatedUser.model_validate(current_user)
