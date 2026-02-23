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

The backend can run with defaults (SQLite) without exporting environment variables:

- `DB_TYPE=sqlite+aiosqlite`
- `DB_NAME=library.db`
- `API_PATH=`
- `API_CORS_ORIGINS=`
- `LOG_LEVEL=WARNING`
- `JWT_SECRET_KEY=change-me-in-production`
- `JWT_ALGORITHM=HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30`

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
- Dependency injection guide: `docs/dependency_injection.md`
- Router auto-registration: `docs/router_registration.md`
