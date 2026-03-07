# Dependency Injection Guide

## Goal

Keep wiring in one place and keep feature modules focused on behavior.

## Current layout

Dependency providers live in `app/core/setup/dependencies.py`.

Main providers:

- `get_db_session`
- `get_unit_of_work`
- `get_auth_repository`
- `get_rbac_repository`
- `get_outbox_repository`
- `get_auth_service`
- `get_rbac_service`
- `get_outbox_service`
- `get_password_service`
- `get_token_service`

Feature-local auth dependencies live in:

- `app/features/auth/dependencies.py`
- `app/features/rbac/dependencies.py`
- `app/core/authorization/dependencies.py`

## Router usage

Routers consume typed dependency aliases instead of constructing services directly.

Example:

```python
@router.get("/roles", response_model=list[RBACRole], **GET_ROLES_DOC)
async def list_roles(
    rbac_service: RBACServiceDependency,
    _authorized_user: RBACRoleAdminAuth,
) -> list[RBACRole]:
    roles = await rbac_service.list_roles()
    return to_role_response_list(roles)
```

## Transaction model

`get_db_session` creates one `AsyncSession` per request.
That same session is reused by repositories and `UnitOfWork`, so one use case runs inside one transaction scope.

Practical effect:

- success path: commit at Unit of Work exit
- failure path: rollback for all pending writes in scope

## Test overrides

Use `app.dependency_overrides` in tests.

```python
from app.core.setup.dependencies import get_db_session
from app.main import app

async def override_db_session():
    async with mock_database.Session() as session:
        yield session

app.dependency_overrides[get_db_session] = override_db_session
```

Clear overrides during teardown:

```python
app.dependency_overrides.clear()
```
