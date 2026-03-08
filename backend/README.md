# backend (FastAPI API)

Reusable FastAPI backend template organized by feature.

For repository-level setup and multi-service Docker flows, see `../README.md`.

## Technical Documentation Map

- `docs/backend_playbook.md`: canonical architecture and engineering rules.
- `docs/foundation_status.md`: canonical snapshot of current backend foundation state and quality gates.
- `docs/README.md`: role-based reading order for AI, reviewer, and requester workflows.
- `docs/operations/*.md`: API/auth/authz/error runtime contracts.
- `docs/architecture/*.md`: DI, UoW, router registration, and OpenAPI design patterns.
- `docs/templates/*.md`: templates to request AI-driven features, integrations, and code changes.

## Development Environment (Local Python)

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

## Runtime Configuration

Default local profile (SQLite):

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

## Run Backend Locally

From repo root:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API docs: `http://localhost:8000/docs`
- Base API namespace: `/v1`

## Migrations and Bootstrap

From `backend/`:

```bash
alembic upgrade head
```

Create a migration:

```bash
alembic revision --autogenerate -m "describe change"
```

Seed RBAC baseline after migrations:

```bash
python -m utils.rbac_bootstrap --admin-username admin --admin-password "StrongSeed9"
```

This bootstrap command:

- upserts base permissions,
- creates missing base roles,
- creates the admin user only if missing,
- ensures admin role assignment.

Base permissions:

- `roles:manage`
- `role_permissions:manage`
- `user_roles:manage`

## Testing and Validation

Run from repo root:

```bash
pytest backend/tests
```

CI-equivalent coverage gate:

```bash
pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100
```

Dockerized backend test run (isolated):

```bash
docker compose -f compose.test.yaml run --rm backend-test
```

## Production Preparation and Run

Before production startup (`APP_ENV=prod`), set strong values for:

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `JWT_ISSUER`
- `JWT_AUDIENCE`

Run production stack from repo root:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

Stop production stack:

```bash
docker compose -f compose.yaml -f compose.prod.yaml down
```

## Template Shape

Current backend layout:

- `app/core`: shared runtime, config, security, authorization, db, setup
- `app/features/auth`: register, login, current-user profile
- `app/features/health`: health endpoint
- `app/features/rbac`: roles, permissions, user-role assignment
- `app/features/outbox`: outbox capability
