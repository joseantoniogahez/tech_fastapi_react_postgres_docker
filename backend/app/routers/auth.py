from fastapi import APIRouter

from app.dependencies import AuthCredentialsDependency, AuthServiceDependency, CurrentActiveUserDependency
from app.schemas.auth import AuthenticatedUser, RegisterUser, Token, UpdateCurrentUser

router = APIRouter(tags=["auth"])


@router.post("/token")
async def login_for_access_token(
    credentials: AuthCredentialsDependency,
    auth_service: AuthServiceDependency,
) -> Token:
    return await auth_service.login(credentials)


@router.post("/users/register", status_code=201)
async def register_user(
    register_data: RegisterUser,
    auth_service: AuthServiceDependency,
) -> AuthenticatedUser:
    return await auth_service.register(register_data)


@router.get("/users/me")
async def read_current_user(current_user: CurrentActiveUserDependency) -> AuthenticatedUser:
    return AuthenticatedUser.model_validate(current_user)


@router.patch("/users/me")
async def update_current_user(
    update_data: UpdateCurrentUser,
    current_user: CurrentActiveUserDependency,
    auth_service: AuthServiceDependency,
) -> AuthenticatedUser:
    return await auth_service.update_current_user(current_user=current_user, update_data=update_data)
