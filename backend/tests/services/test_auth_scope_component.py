from unittest.mock import AsyncMock, MagicMock, patch

from app.const.permission import PermissionScope
from app.const.settings import AuthSettings
from app.services.auth import AuthService


def _build_service() -> AuthService:
    repository = MagicMock()
    repository.get_by_username = AsyncMock()
    repository.username_exists = AsyncMock(return_value=False)
    repository.create = AsyncMock()
    repository.update = AsyncMock()
    repository.get_user_permission_scope = AsyncMock(return_value=None)
    repository.user_has_permission = AsyncMock()

    unit_of_work = MagicMock()
    unit_of_work.__aenter__ = AsyncMock(return_value=unit_of_work)
    unit_of_work.__aexit__ = AsyncMock(return_value=None)

    settings = AuthSettings(
        JWT_SECRET_KEY="unit-test-secret",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
    )
    return AuthService(auth_repository=repository, unit_of_work=unit_of_work, auth_settings=settings)


def test_scope_evaluator_defensive_fallback_returns_false_for_unknown_required_scope() -> None:
    service = _build_service()

    # Simula una futura expansión de scopes para ejecutar la rama defensiva actual.
    with patch.dict("app.services.auth.PERMISSION_SCOPE_RANK", {"regional": 2}, clear=False):
        allowed = service._scope_satisfies_requirement(
            granted_scope=PermissionScope.ANY,
            required_scope="regional",
            user_id=1,
            resource_owner_id=1,
            user_tenant_id=1,
            resource_tenant_id=1,
        )

    assert allowed is False
