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

From repo root on Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -c "import sys; assert sys.version_info[:3] == (3, 14, 6)"
.\.venv\Scripts\python.exe -m pip install pip==26.2.1
.\.venv\Scripts\python.exe scripts\update_python_tooling_lock.py
.\.venv\Scripts\python.exe -m pip install --requirement pylock.windows-x86_64.toml
```

See [`../docs/ai/python_tooling.md`](../docs/ai/python_tooling.md) for lock checksums, the exact
POSIX/Ubuntu flow, dependency inventory, audit commands, and platform boundaries.

## Runtime Configuration

Default local profile when backend environment variables are unset outside Docker (SQLite):

- `APP_ENV=local`
- `DB_TYPE=sqlite+aiosqlite`
- `DB_NAME=app.db`
- `API_PATH=`
- `API_CORS_ORIGINS=`
- `LOG_LEVEL=WARNING`
- `READINESS_TIMEOUT_SECONDS=2`
- `READINESS_MAX_CONCURRENCY=4`
- `RATE_LIMIT_ENABLED=true`
- `RATE_LIMIT_STORAGE=memory`
- `RATE_LIMIT_LOGIN=10`
- `RATE_LIMIT_REGISTER=5`
- `RATE_LIMIT_WINDOW_SECONDS=60`

`APP_ENV` accepts `local`, `test`, `development`, `staging`, or `production`; `dev` and `prod`
normalize to their long forms and unknown values fail startup validation. `/docs`, `/redoc`, and
`/openapi.json` exist only in `local`, `test`, and `development`. The frontend contract exporter
uses `test` explicitly, so its artifact does not depend on the caller's shell environment.

`API_CORS_ORIGINS` is a comma-separated list of bare HTTP(S) origins. Credentialed CORS rejects
wildcards, paths, queries, fragments, credentials, and invalid hosts or ports, and uses explicit
method/header allowlists.

JWT defaults for `local/test`:

- `JWT_SECRET_KEY=local-development-jwt-secret-32-bytes`
- `JWT_ALGORITHM=HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `JWT_ISSUER=fastapi-template`
- `JWT_AUDIENCE=fastapi-template-api`

Repository-level Docker Compose uses `.env` values from `.env_examples`, requires PostgreSQL, and
runs against `DB_TYPE=postgresql+asyncpg` by default with `DB_HOST=system_db`, `DB_NAME=main_db`.
Local, test, and development processes outside Compose may use SQLite; staging/production settings
reject it.

`GET /v1/health` is dependency-free liveness. `GET /v1/readiness` checks the configured database
and any enabled registered dependency, returning a typed `200` or `503` without provider details.
Use readiness for traffic admission, never as a container restart signal.

Login and registration use fixed-window rate limiting. Local Python defaults to memory; Compose
uses authenticated Redis. Staging/production require enabled shared Redis and explicit thresholds,
and fail startup on missing or insecure configuration. See
`docs/operations/rate_limiting.md` for headers, errors, TLS/plaintext policy, and secret handling.

For network databases, set:

- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`

## Run Backend Locally

From repo root:

```powershell
$env:PYTHONPATH = "backend"; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On POSIX, use
`PYTHONPATH=backend ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.

- API docs in `local`, `test`, or `development`: `http://localhost:8000/docs`
- Base API namespace: `/v1`

## Migrations and Bootstrap

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

Create a migration:

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini revision --autogenerate -m "describe change"
```

Seed RBAC baseline after migrations:

```powershell
$env:PYTHONPATH = "backend"; .\.venv\Scripts\python.exe -m utils.rbac_bootstrap --admin-username admin --admin-password "StrongSeed9"
```

If you started services with `docker compose up --build` and want to run bootstrap from local
PowerShell without entering the container, run from the repository root:

```powershell
$env:PYTHONPATH = "backend"; $env:DB_TYPE = "postgresql+asyncpg"; $env:DB_HOST = "localhost"; $env:DB_PORT = "5432"; $env:DB_NAME = "main_db"; $env:DB_USER = "my_admin"; $env:DB_PASSWORD = "{{DB_PASSWORD}}"; .\.venv\Scripts\python.exe -m utils.rbac_bootstrap --admin-username admin --admin-password "StrongSeed9"
```

macOS/Linux (bash/zsh) equivalent:

```bash
PYTHONPATH=backend DB_TYPE="postgresql+asyncpg" DB_HOST="localhost" DB_PORT="5432" DB_NAME="main_db" DB_USER="my_admin" DB_PASSWORD="{{DB_PASSWORD}}" ./.venv/bin/python -m utils.rbac_bootstrap --admin-username admin --admin-password "StrongSeed9"
```

Note: use `DB_HOST=localhost` for host-side execution.

This bootstrap command:

- upserts base permissions,
- creates missing base roles,
- creates the admin user only if missing,
- ensures admin role assignment.

Base permissions:

- `audit_logs:read`
- `roles:manage`
- `role_permissions:manage`
- `user_roles:manage`
- `users:manage`

## Testing and Validation

Run from repo root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
```

CI-equivalent coverage gate:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100
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
- `REDIS_PASSWORD`
- `RATE_LIMIT_LOGIN`
- `RATE_LIMIT_REGISTER`
- `RATE_LIMIT_WINDOW_SECONDS`

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
- `app/features/audit_log`: administrator audit log review
- `app/features/health`: liveness and readiness endpoints
- `app/features/rbac`: roles, permissions, user-role assignment
- `app/features/outbox`: outbox capability
