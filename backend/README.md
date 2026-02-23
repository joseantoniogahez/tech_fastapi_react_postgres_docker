# backend (FastAPI API)

Backend service for the Books App.

For full-stack orchestration and repository-level setup, see `../README.md`.
For frontend-only setup, see `../books-app/README.md`.

## Quick Start (Unit Tests + Basic Local Run)

This project uses a repository-level virtual environment (`../.venv`).

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

Install dependencies (backend runtime + backend tests + repo tooling):

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run backend unit tests:

```bash
pytest backend/tests
```

Run only one test module or a subset:

```bash
pytest backend/tests/routers/test_auth.py
pytest backend/tests -k "rbac or token"
```

Coverage (from `backend/`):

```bash
cd backend
pytest --cov-report term-missing:skip-covered --cov app
```

## Basic Backend Configuration

The backend can run with defaults (SQLite) for API/DB settings:

- `APP_ENV=local`
- `DB_TYPE=sqlite+aiosqlite`
- `DB_NAME=library.db`
- `API_PATH=`
- `API_CORS_ORIGINS=`
- `LOG_LEVEL=WARNING`

JWT settings default for `local/test`:

- `JWT_SECRET_KEY=local-dev-jwt-secret`
- `JWT_ALGORITHM` (for example `HS256`)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (integer > 0)

When `APP_ENV=prod` (or `production` / `staging`), JWT settings are required from environment variables and validated at startup.

If `DB_TYPE` starts with `sqlite`, only `DB_TYPE` and `DB_NAME` are required.

If `DB_TYPE` is a network database driver (for example `postgresql+asyncpg`), set all DB network variables:

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

API docs: `http://localhost:8000/docs`

## Migrations

From `backend/`:

```bash
alembic upgrade head
```

Create a new migration:

```bash
alembic revision --autogenerate -m "describe change"
```

## Documentation By Topic

- Docs index: `docs/README.md`
- API endpoints: `docs/api_endpoints.md`
- Authentication and account management: `docs/authentication.md`
- RBAC permission matrix: `docs/authorization_matrix.md`
- Error mapping and payload format: `docs/error_mapping.md`
- Unit of Work transaction boundary and atomic write policy: `docs/unit_of_work.md`
- OpenAPI documentation pattern: `docs/openapi_documentation.md`
- Dependency injection guide: `docs/dependency_injection.md`
- Router auto-registration: `docs/router_registration.md`
