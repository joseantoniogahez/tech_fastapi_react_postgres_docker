from typing import cast
from unittest.mock import AsyncMock, MagicMock

from app.const.settings import AuthSettings
from app.models.user import User
from app.services.auth import AuthService
from app.services.password_service import PasswordServicePort
from app.services.permission_evaluator import PermissionEvaluatorPort
from app.services.token_service import TokenServicePort


def assert_unit_of_work_scope_committed(unit_of_work: object) -> None:
    unit_of_work_mock = cast(MagicMock, unit_of_work)
    unit_of_work_enter = cast(AsyncMock, unit_of_work_mock.__aenter__)
    unit_of_work_exit = cast(AsyncMock, unit_of_work_mock.__aexit__)
    unit_of_work_enter.assert_awaited_once_with()
    unit_of_work_exit.assert_awaited_once_with(None, None, None)


def _build_repository_mock() -> MagicMock:
    repository = MagicMock()
    repository.get_by_username = AsyncMock()
    repository.username_exists = AsyncMock(return_value=False)
    repository.create = AsyncMock()
    repository.update = AsyncMock()
    repository.get_rbac_version = AsyncMock(
        return_value="0" * 64,
    )
    repository.get_user_permission_scope = AsyncMock(return_value=None)
    repository.user_has_permission = AsyncMock()
    return repository


def _build_unit_of_work_mock() -> MagicMock:
    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)
    return unit_of_work


def build_service(
    repository: MagicMock | None = None,
    *,
    permission_evaluator: PermissionEvaluatorPort | None = None,
    token_service: TokenServicePort | None = None,
    password_service: PasswordServicePort | None = None,
    permission_scope_cache: dict[tuple[int, str], str | None] | None = None,
) -> tuple[AuthService, MagicMock]:
    repo = repository or _build_repository_mock()
    unit_of_work = _build_unit_of_work_mock()
    settings = AuthSettings(
        JWT_SECRET_KEY="unit-test-secret",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
        JWT_ISSUER="unit-test-issuer",
        JWT_AUDIENCE="unit-test-audience",
    )
    return (
        AuthService(
            auth_repository=repo,
            unit_of_work=unit_of_work,
            auth_settings=settings,
            permission_evaluator=permission_evaluator,
            token_service=token_service,
            password_service=password_service,
            permission_scope_cache=permission_scope_cache,
        ),
        repo,
    )


def build_user(
    service: AuthService,
    *,
    user_id: int = 1,
    username: str = "john",
    password: str = "StrongPass1",
    disabled: bool = False,
    tenant_id: int | None = None,
) -> User:
    return User(
        id=user_id,
        username=username,
        hashed_password=service.password_service.hash_password(password),
        disabled=disabled,
        tenant_id=tenant_id,
    )
