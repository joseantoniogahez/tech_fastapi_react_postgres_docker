# Books App (FastAPI + Next.js + PostgreSQL)

Full-stack sample application for managing books and authors.

- Backend: FastAPI + SQLAlchemy (async) + Alembic
- Frontend: Next.js (App Router, React 19)
- Database: PostgreSQL 18
- Orchestration: Docker Compose

## README files in this project

- `README.md` (this file): repository-level architecture and multi-service run flow.
- `backend/README.md`: backend-only setup, API behavior, migrations, and backend tests.
- `books-app/README.md`: frontend-only setup, scripts, tests, and API client configuration.

## Project Structure

- `backend/`: FastAPI API, models, services, migrations, backend tests
- `books-app/`: Next.js UI and frontend tests
- `compose.yaml`: shared multi-container stack (base)
- `compose.override.yaml`: local development overrides loaded automatically by `docker compose`
- `compose.test.yaml`: isolated services for backend/frontend test runs
- `compose.prod.yaml`: production overrides (restart policy, persistent DB volume, prod project name)
- `.env_examples`: environment template used to generate `.env`
- `.env`: container configuration used by compose

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Optional for local non-Docker workflows:
  - Python 3.14.3
  - Node.js 22+

## Environment Configuration

Use `.env_examples` as the template for the root `.env` file consumed by `docker compose`.

```bash
# macOS/Linux
cp .env_examples .env

# Windows PowerShell
Copy-Item .env_examples .env
```

Variable details are documented in `.env_examples`.

## Run Full Stack With Docker

From repo root:

```bash
docker compose up --build
```

Endpoints:
- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

Notes:
- Backend container runs Alembic migrations during startup (`backend/prestart.sh`).
- Frontend API target is controlled by `NEXT_PUBLIC_API_ORIGIN` and `NEXT_PUBLIC_API_BASE_PATH`.

## Run Tests With Docker Compose

From repo root:

```bash
# Backend tests
docker compose -f compose.test.yaml run --rm backend-test

# Frontend tests
docker compose -f compose.test.yaml run --rm frontend-test

# Both (sequential)
docker compose -f compose.test.yaml run --rm backend-test && docker compose -f compose.test.yaml run --rm frontend-test
```

`compose.test.yaml` sets `name: books-tests`, so test runs use a separate Compose project from local dev.

## Run Production Profile With Docker Compose

From repo root:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

Stop production stack:

```bash
docker compose -f compose.yaml -f compose.prod.yaml down
```

`compose.prod.yaml` sets `name: books-prod`, so production resources stay isolated from dev/test projects.

If you previously created the production volume with an old mount path and `database` keeps restarting, recreate the prod volume:

```bash
docker compose -f compose.yaml -f compose.prod.yaml down -v
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

## Integration Caveat (`/api` Path)

- Backend routes are declared as `/books/`, `/authors/`, and `/health`.
- Frontend defaults to calling `/api/...`.
- `API_PATH` configures FastAPI `root_path` metadata, but does not mount routes under `/api` by itself.
- If clients call `/api/...`, use a reverse-proxy rewrite or configure frontend base path to `/`.

## Repository Tooling (Root)

This repository uses a root virtual environment for repo hooks and backend-related tooling:

```bash
# from repo root
python -m venv .venv
```

Activate the virtualenv:

```bash
# Windows PowerShell
.venv/Scripts/Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies and hooks:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pre-commit install --install-hooks
```

Run repository hooks:

```bash
pre-commit run --all-files
```

If a dependency version used by the `mypy` hook changes in `backend/requirements.txt` or `backend/tests/requirements.txt`, update the matching version in `.pre-commit-config.yaml`.
