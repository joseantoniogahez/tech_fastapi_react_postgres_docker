from fastapi import APIRouter

from app.dependencies.authentication import AuthCredentialsDependency, CurrentActiveUserDependency
from app.dependencies.authorization import AuthenticatedReadAccessDependency
from app.dependencies.services import AuthServiceDependency
from app.openapi.auth import (
    LOGIN_FOR_ACCESS_TOKEN_DOC,
    READ_CURRENT_USER_DOC,
    REGISTER_USER_DOC,
    UPDATE_CURRENT_USER_DOC,
    RegisterUserPayload,
    UpdateCurrentUserPayload,
)
from app.schemas.api.auth import AuthenticatedUser, Token
from app.schemas.application.auth import LoginCommand, RegisterUserCommand, UpdateCurrentUserCommand

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=Token, **LOGIN_FOR_ACCESS_TOKEN_DOC)
async def login_for_access_token(
    credentials: AuthCredentialsDependency,
    auth_service: AuthServiceDependency,
) -> Token:
    token = await auth_service.login(LoginCommand.from_api(credentials))
    return Token.from_application(token)


@router.post("/users/register", response_model=AuthenticatedUser, **REGISTER_USER_DOC)
async def register_user(
    auth_service: AuthServiceDependency,
    register_data: RegisterUserPayload,
) -> AuthenticatedUser:
    user = await auth_service.register(RegisterUserCommand.from_api(register_data))
    return AuthenticatedUser.model_validate(user)


@router.get("/users/me", response_model=AuthenticatedUser, **READ_CURRENT_USER_DOC)
async def read_current_user(current_user: AuthenticatedReadAccessDependency) -> AuthenticatedUser:
    return AuthenticatedUser.model_validate(current_user)


@router.patch("/users/me", response_model=AuthenticatedUser, **UPDATE_CURRENT_USER_DOC)
async def update_current_user(
    current_user: CurrentActiveUserDependency,
    auth_service: AuthServiceDependency,
    update_data: UpdateCurrentUserPayload,
) -> AuthenticatedUser:
    updated_user = await auth_service.update_current_user(
        current_user=current_user,
        update_data=UpdateCurrentUserCommand.from_api(update_data),
    )
    return AuthenticatedUser.model_validate(updated_user)
