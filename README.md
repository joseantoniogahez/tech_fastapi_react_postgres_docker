# Books App (FastAPI + Next.js + PostgreSQL)

Full-stack sample application for managing books and authors.

- Backend: FastAPI + SQLAlchemy (async) + Alembic
- Frontend: Next.js (App Router, React 19)
- Database: PostgreSQL 18
- Orchestration: Docker Compose

## Project Structure

- `backend/`: FastAPI API, models, services, migrations, backend tests
- `books-app/`: Next.js UI and frontend tests
- `docker-compose.yaml`: multi-container local stack
- `.env_examples`: environment template used to generate `.env`
- `.env`: container configuration used by compose

## Features

### Backend API

- `GET /books/`
  - Returns all books with embedded author
  - Supports `author_id` query param for filtering
- `POST /books/`
  - Creates a book
  - Creates author if needed (based on payload)
- `PUT /books/{id}`
  - Updates a book
- `DELETE /books/{id}`
  - Deletes a book
- `GET /authors/`
  - Returns all authors

Book `status` values:
- `published`
- `draft`

### Frontend

- List books
- Filter books by author
- Create/update/delete books
- Create a new author from the book form
- Error toast handling for request failures

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Optional for non-Docker local runs:
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

Variable groups and detailed descriptions live in `.env_examples`.
For frontend API calls, configure `NEXT_PUBLIC_API_ORIGIN` (for example `http://localhost:8000`) and `NEXT_PUBLIC_API_BASE_PATH` (for example `/api` or `/`).

## Run With Docker

From repo root:

```bash
docker compose up --build
```

Endpoints:
- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

Notes:
- Containers run Alembic migrations during backend startup (`backend/prestart.sh`).
- Frontend API target is configured via `NEXT_PUBLIC_API_ORIGIN` + `NEXT_PUBLIC_API_BASE_PATH`.

## Backend: Local Development and Tests

This repository uses a local Python environment in the repo root:

- `.venv`: repository tooling + backend test dependencies

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

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pre-commit install --install-hooks
```

Note:
- If a package version used by the `mypy` hook `additional_dependencies` is updated in `backend/requirements.txt` (or `backend/tests/requirements.txt` for test imports), update the same version in `.pre-commit-config.yaml` to keep pre-commit type-checking aligned with the project environment.

## Local Commands

Backend tests:

```bash
# Windows PowerShell
.venv/Scripts/Activate.ps1

# macOS/Linux
source .venv/bin/activate

pytest
```

Repository hooks:

```bash
# Windows PowerShell
.venv/Scripts/Activate.ps1

# macOS/Linux
source .venv/bin/activate
pre-commit run --all-files
```

## Frontend: Local Development and Tests

```bash
cd books-app
npm install
# Optional (recommended for local frontend + local backend):
# set NEXT_PUBLIC_API_ORIGIN=http://localhost:8000   # Windows PowerShell
# set NEXT_PUBLIC_API_BASE_PATH=/api                 # Windows PowerShell
# export NEXT_PUBLIC_API_ORIGIN=http://localhost:8000 # macOS/Linux
# export NEXT_PUBLIC_API_BASE_PATH=/api               # macOS/Linux
npm run dev
```

Frontend tests:

```bash
npm test
```

## Known Caveats

- Backend routes are declared as `/books/` and `/authors/`, while frontend requests use `/api/...`.
- `API_PATH` is currently used as FastAPI `root_path`, which does not mount routes at `/api` by itself.
- Depending on deployment/proxy setup, requests to `/api/...` may require an explicit reverse proxy rewrite.
