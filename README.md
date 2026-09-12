# FastAPI + React + PostgreSQL Docker Template

Full-stack template application with JWT authentication and RBAC.

- Backend: FastAPI + SQLAlchemy (async) + Alembic
- Frontend: Vite + React 19 + TypeScript
- Database: PostgreSQL 18.2 (`postgres:18.2`)
- Authentication rate-limit store: Redis 8.8.1 (`redis:8.8.1-alpine`)
- Orchestration: Docker Compose

## README Map

- `README.md` (this file): repository architecture and multi-service run flow.
- `backend/README.md`: backend-only setup, API behavior, migrations, and backend tests.
- `frontend/README.md`: frontend-only setup, scripts, tests, and API client configuration.
- `AGENTS.md`: AI assistant operating guide for this starter kit.
- `docs/ai/start_new_project.md`: new-project bootstrap workflow for turning this starter kit into
  a named application.

## Project Structure

- `backend/`: FastAPI API, models, services, migrations, backend tests
- `backend/docs/`: backend documentation (API endpoints, auth, RBAC, DI, OpenAPI pattern)
- `frontend/`: React SPA and frontend tests
- `frontend/docs/`: frontend documentation (routing, API sync, runtime config, quality gates)
- `docs/ai/`: repository-level AI request templates and new-project bootstrap instructions
- `scripts/`: repository-level developer and AI workflow helpers
- `.github/workflows/ci.yaml`: CI validation for repository hooks, backend, and frontend
- `compose.yaml`: base multi-container stack
- `compose.override.yaml`: local development overrides loaded automatically by `docker compose`
- `compose.test.yaml`: isolated services for backend/frontend test runs
- `compose.prod.yaml`: production overrides (restart policy, persistent DB volume, prod project name)
- `.env_examples`: environment template used to create `.env`
- `.env`: environment file used by compose

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Optional for local non-Docker workflows:
  - Python 3.14.6
  - Node.js 22 (`>=22.22.2 <23`; `22.23.1` is pinned in Docker/CI)
  - npm 12.0.x (`12.0.1` is the reproducible execution pin)

## Environment Setup

Create `.env` from `.env_examples` at repository root:

```bash
# macOS/Linux
cp .env_examples .env

# Windows PowerShell
Copy-Item .env_examples .env
```

See `.env_examples` for variable descriptions.

## Use This As a New Project Starter

Start with the detailed guide:

```bash
docs/ai/start_new_project.md
```

Quick flow:

```powershell
# preview identity changes
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows."

# apply after reviewing the preview
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows." --write
```

On POSIX, replace `.\.venv\Scripts\python.exe` with `./.venv/bin/python`.

Then review `git diff`, create `.env` from `.env_examples`, run the validation gates listed in
`docs/ai/start_new_project.md`, and start the stack with `docker compose up --build`.

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
- Frontend API target is controlled by `VITE_API_ORIGIN` and `VITE_API_BASE_PATH`.
- Vite env vars are baked into build output; rebuild frontend image after changing them.

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

`compose.test.yaml` sets `name: tech-tests`, so test resources stay isolated from local development.

## GitHub Actions CI

The repository includes a GitHub Actions workflow at `.github/workflows/ci.yaml` for push and pull request validation.

It runs three independent quality gates on the accepted Ubuntu 24.04, Python 3.14.6, Node.js
22.23.1, npm 12.0.1, Docker 29.6.2, and Compose 5.3.1 matrix:

- `governance`: validates skills, documentation contracts, dependency audits, pre-push hooks, and
  all five supported Compose render forms.
- `backend`: runs mypy, dependency checks, and the 100% backend coverage gate.
- `frontend`: runs the dependency audit, quality gate, smoke e2e, production build, and a real HTTP
  security-header smoke against the production image.

The separate `Release validation` workflow runs on pull requests and supports manual execution.
It validates disposable PostgreSQL/Redis services, production images, and a new application
bootstrapped from the checked-out snapshot. See
[`docs/ai/release_validation.md`](docs/ai/release_validation.md) for its execution and reuse boundary.

## Run Production Profile (Docker Compose)

From repository root:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

Production JWT note:

- `compose.prod.yaml` sets `APP_ENV=prod`.
- Define `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_ISSUER`, and `JWT_AUDIENCE` in `.env` before starting.
- Define `REDIS_PASSWORD`, `RATE_LIMIT_LOGIN`, `RATE_LIMIT_REGISTER`, and
  `RATE_LIMIT_WINDOW_SECONDS`. Redis remains private to the Compose network and its password is
  mounted as a secret rather than rendered into service environment output.

Stop production stack:

```bash
docker compose -f compose.yaml -f compose.prod.yaml down
```

`compose.prod.yaml` sets `name: tech-prod`, so production resources stay isolated from dev/test projects.

If production `database` keeps restarting due to an old volume mount path, recreate the production volume:

**This deletes all Compose-managed database data.** Do not run it until a custom-format PostgreSQL
backup has a matching SHA-256, is encrypted outside the repository, and has passed the isolated
restore drill in `backend/docs/operations/postgresql_backups.md`. Otherwise stop and recover the
volume instead.

```bash
docker compose -f compose.yaml -f compose.prod.yaml down -v
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

## API Base Path Contract (`/v1`)

- Backend routes are mounted under `/v1`.
- Frontend default is `VITE_API_BASE_PATH=/v1`.
- `API_PATH` controls FastAPI `root_path` metadata for proxy deployments only; it does not remount routes.

## Repository Tooling (Root)

The repository uses a root virtual environment for shared tooling and hooks.

Local `pre-commit` hooks depend on more than the root Python environment. The exact matrix, lock
checksums, inventory, and Windows/POSIX commands are in
[`docs/ai/python_tooling.md`](docs/ai/python_tooling.md).

- Python 3.14.6 for Python-based hooks
- Node.js 22.23.1 and npm 12.0.1 for `frontend` ESLint and typecheck hooks
- Docker Desktop (or Docker Engine + Compose plugin) for `hadolint` and `docker compose config` hooks
- Compose validation hooks use the committed, non-secret `.env_examples` fixture. A local `.env`
  copied from it is still required when running the application stack.

Create the environment:

```powershell
# from repo root
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -c "import sys; assert sys.version_info[:3] == (3, 14, 6)"
```

Install the locked Windows environment and hooks:

```powershell
.\.venv\Scripts\python.exe -m pip install pip==26.2.1
.\.venv\Scripts\python.exe scripts\update_python_tooling_lock.py
.\.venv\Scripts\python.exe -m pip install --requirement pylock.windows-x86_64.toml
npm --prefix frontend ci
.\.venv\Scripts\python.exe -m pre_commit install --install-hooks --hook-type pre-commit --hook-type pre-push
```

The root `requirements.txt` is the umbrella input manifest. The platform lock contains every
resolved transitive dependency and artifact hash; do not use the Windows lock on POSIX.

Before running hooks, make sure Docker is running so local Docker-based hooks can start successfully.

Run repository hooks:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run --all-files
```

Run heavier pre-push hooks locally:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run --all-files --hook-stage pre-push
```

## AI Workflow Helpers

Preview feature scaffolds:

```powershell
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run full-stack audit-log --route /admin/audit-log --with-model
```

Preview new-app identity bootstrap:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows."
```
