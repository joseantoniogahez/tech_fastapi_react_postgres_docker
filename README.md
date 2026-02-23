# Books App (FastAPI + Next.js + PostgreSQL)

Full-stack sample application for managing books and authors.

- Backend: FastAPI + SQLAlchemy (async) + Alembic
- Frontend: Next.js (App Router, React 19)
- Database: PostgreSQL 18
- Orchestration: Docker Compose

## README Map

- `README.md` (this file): repository architecture and multi-service run flow.
- `backend/README.md`: backend-only setup, API behavior, migrations, and backend tests.
- `books-app/README.md`: frontend-only setup, scripts, tests, and API client configuration.

## Project Structure

- `backend/`: FastAPI API, models, services, migrations, backend tests
- `backend/docs/`: backend documentation (API endpoints, auth, RBAC, DI, OpenAPI pattern)
- `books-app/`: Next.js UI and frontend tests
- `compose.yaml`: base multi-container stack
- `compose.override.yaml`: local development overrides loaded automatically by `docker compose`
- `compose.test.yaml`: isolated services for backend/frontend test runs
- `compose.prod.yaml`: production overrides (restart policy, persistent DB volume, prod project name)
- `.env_examples`: environment template used to create `.env`
- `.env`: environment file used by compose

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Optional for local non-Docker workflows:
  - Python 3.14.3
  - Node.js 22+

## Environment Setup

Create `.env` from `.env_examples` at repository root:

```bash
# macOS/Linux
cp .env_examples .env

# Windows PowerShell
Copy-Item .env_examples .env
```

See `.env_examples` for variable descriptions.

## Run Full Stack (Docker)

From repository root:

```bash
docker compose up --build
```

Endpoints:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

Notes:

- Backend runs Alembic migrations during startup (`backend/prestart.sh`).
- `compose.override.yaml` is loaded automatically for local runs and enables backend hot reload via bind mount.
- Frontend API target is controlled by `NEXT_PUBLIC_API_ORIGIN` and `NEXT_PUBLIC_API_BASE_PATH`.
- `NEXT_PUBLIC_*` values are baked into frontend build output; rebuild frontend image after changing them.

## Run Tests (Docker Compose)

From repository root:

```bash
# Backend tests
docker compose -f compose.test.yaml run --rm backend-test

# Frontend tests
docker compose -f compose.test.yaml run --rm frontend-test

# Both (sequential)
docker compose -f compose.test.yaml run --rm backend-test && docker compose -f compose.test.yaml run --rm frontend-test
```

`compose.test.yaml` sets `name: books-tests`, so test resources stay isolated from local development.

## Run Production Profile (Docker Compose)

From repository root:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

Stop production stack:

```bash
docker compose -f compose.yaml -f compose.prod.yaml down
```

`compose.prod.yaml` sets `name: books-prod`, so production resources stay isolated from dev/test projects.

If production `database` keeps restarting due to an old volume mount path, recreate the production volume:

```bash
docker compose -f compose.yaml -f compose.prod.yaml down -v
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

## API Base Path Integration (`/api`)

- Backend routes are declared as `/books/`, `/authors/`, and `/health`.
- Frontend defaults to calling `/api/...`.
- `API_PATH` sets FastAPI `root_path` metadata only; it does not mount routes under `/api`.
- If clients call `/api/...`, use a reverse-proxy rewrite or set frontend base path to `/`.

## Repository Tooling (Root)

The repository uses a root virtual environment for shared tooling and hooks.

Create and activate:

```bash
# from repo root
python -m venv .venv

# Windows PowerShell
.venv/Scripts/Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install tooling:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pre-commit install --install-hooks
```

Run repository hooks:

```bash
pre-commit run --all-files
```

If a dependency version used by the `mypy` hook changes in `backend/requirements.txt` or `backend/tests/requirements.txt`,
update the matching version in `.pre-commit-config.yaml`.
