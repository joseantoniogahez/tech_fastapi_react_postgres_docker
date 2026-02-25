from fastapi import APIRouter

from app.dependencies.authentication import AuthCredentialsDependency, CurrentActiveUserDependency
from app.dependencies.services import AuthServiceDependency
from app.openapi.auth import (
    LOGIN_FOR_ACCESS_TOKEN_DOC,
    READ_CURRENT_USER_DOC,
    REGISTER_USER_DOC,
    UPDATE_CURRENT_USER_DOC,
    RegisterUserPayload,
    UpdateCurrentUserPayload,
)
from app.schemas.auth import AuthenticatedUser, Token

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=Token, **LOGIN_FOR_ACCESS_TOKEN_DOC)
async def login_for_access_token(
    credentials: AuthCredentialsDependency,
    auth_service: AuthServiceDependency,
) -> Token:
    return await auth_service.login(credentials)


@router.post("/users/register", response_model=AuthenticatedUser, **REGISTER_USER_DOC)
async def register_user(
    auth_service: AuthServiceDependency,
    register_data: RegisterUserPayload,
) -> AuthenticatedUser:
    return await auth_service.register(register_data)


@router.get("/users/me", response_model=AuthenticatedUser, **READ_CURRENT_USER_DOC)
async def read_current_user(current_user: CurrentActiveUserDependency) -> AuthenticatedUser:
    return AuthenticatedUser.model_validate(current_user)


@router.patch("/users/me", response_model=AuthenticatedUser, **UPDATE_CURRENT_USER_DOC)
async def update_current_user(
    current_user: CurrentActiveUserDependency,
    auth_service: AuthServiceDependency,
    update_data: UpdateCurrentUserPayload,
) -> AuthenticatedUser:
    return await auth_service.update_current_user(current_user=current_user, update_data=update_data)
