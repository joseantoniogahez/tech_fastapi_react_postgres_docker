# backend (FastAPI API)

Reusable FastAPI backend template organized by feature.

For repository-level setup, see `../README.md`.

## Quick Start

This project uses the repository virtual environment `../.venv`.

From repo root:

```bash
python -m venv .venv
```

Activate:

```bash
# Windows PowerShell
.venv/Scripts/Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run tests:

```bash
pytest backend/tests
```

## Default Configuration

The backend can run locally with SQLite defaults:

- `APP_ENV=local`
- `DB_TYPE=sqlite+aiosqlite`
- `DB_NAME=app.db`
- `API_PATH=`
- `API_CORS_ORIGINS=`
- `LOG_LEVEL=WARNING`

JWT defaults for `local/test`:

- `JWT_SECRET_KEY=local-dev-jwt-secret`
- `JWT_ALGORITHM=HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `JWT_ISSUER=fastapi-template`
- `JWT_AUDIENCE=fastapi-template-api`

For network databases, set:

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`

## Run Locally

From repo root:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Docs: `http://localhost:8000/docs`

Base API namespace: `/v1`

## Migrations

From `backend/`:

```bash
alembic upgrade head
```

Create a migration:

```bash
alembic revision --autogenerate -m "describe change"
```

## RBAC Bootstrap

After migrations, seed the RBAC baseline:

```bash
cd backend
python -m utils.rbac_bootstrap --admin-username admin --admin-password "StrongSeed9"
```

This command:

- upserts base permissions,
- creates missing base roles,
- creates the admin user only if missing,
- ensures the admin role assignment.

Current base permissions:

- `roles:manage`
- `role_permissions:manage`
- `user_roles:manage`

Environment variables:

- `RBAC_BOOTSTRAP_ADMIN_USERNAME` default: `admin`
- `RBAC_BOOTSTRAP_ADMIN_PASSWORD` required only when creating the admin user

## Template Shape

The backend is organized as:

- `app/core`: shared runtime, config, security, authorization, DB, setup
- `app/features/auth`: register, login, current-user profile
- `app/features/health`: health endpoint
- `app/features/rbac`: roles, permissions, user-role assignment
- `app/features/outbox`: outbox capability

## Documentation

- `docs/README.md`
- `docs/operations/api_endpoints.md`
- `docs/operations/authentication.md`
- `docs/operations/authorization_matrix.md`
- `docs/operations/error_mapping.md`
