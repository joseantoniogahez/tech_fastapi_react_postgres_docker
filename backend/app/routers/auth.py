from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import AuthServiceDependency
from app.schemas.auth import Credentials, Token

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
    credentials = Credentials(username=form_data.username, password=form_data.password)
    access_token = await auth_service.authenticate(credentials)
    if access_token is None:
        raise INVALID_CREDENTIALS_EXCEPTION

    return Token(access_token=access_token)
