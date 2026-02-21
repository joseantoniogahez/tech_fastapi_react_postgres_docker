# backend (FastAPI API)

Backend service for the Books App.

For full-stack orchestration and repository-level setup, see `../README.md`.
For frontend-only setup, see `../books-app/README.md`.

## Tech Stack

- FastAPI
- SQLAlchemy (async)
- Alembic
- PostgreSQL (runtime target)
- SQLite (local fallback for backend-only runs/tests)

## Backend Scope

- API endpoints for books and authors
- Persistence models and service layer
- Database migrations
- Backend API tests

## API Endpoints

- `GET /health`
- `GET /books/`
  - Supports `author_id` query param for filtering
- `POST /books/`
  - Creates a book
  - Creates author if needed (based on payload)
- `PUT /books/{id}`
- `DELETE /books/{id}`
- `GET /authors/`

Book `status` values:
- `published`
- `draft`

## Runtime Configuration

Primary environment variables:

- `API_PATH` (FastAPI `root_path`)
- `API_CORS_ORIGINS` (comma-separated origins)
- `LOG_LEVEL`
- `DB_TYPE`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`

Behavior:

- If required `DB_*` variables are present, backend connects to PostgreSQL.
- If not, backend falls back to `backend/local_db.env` (`sqlite+aiosqlite`).

## Local Setup

This repository keeps a root virtual environment (`.venv`) for backend tooling and tests.

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

## Run Backend Locally

From repo root:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open docs at `http://localhost:8000/docs`.

## Migrations

From `backend/`:

```bash
alembic upgrade head
```

Create a new migration:

```bash
alembic revision --autogenerate -m "describe change"
```

## Tests

From repo root:

```bash
pytest backend/tests
```

### Coverage with `pytest-cov`

`pytest-cov` is included in `backend/tests/requirements.txt`.

Install backend test dependencies from repo root:

```bash
python -m pip install -r backend/tests/requirements.txt
```

Run coverage from `backend/`:

```bash
cd backend
pytest --cov-report term-missing:skip-covered --cov app
```

What this command does:

- `--cov app`: measures coverage for the `app` package.
- `--cov-report term-missing`: prints a terminal table and shows uncovered line numbers.
- `:skip-covered`: hides files already at 100% so you can focus on missing lines.

How to read the report columns:

- `Stmts`: total executable statements in a file.
- `Miss`: statements not executed by tests.
- `Cover`: coverage percentage for that file.
- `Missing`: exact line numbers that still need tests.
