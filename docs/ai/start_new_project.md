# Start a New Project From This Starter Kit

This repository is ready to use as a governed starter for new FastAPI, React, PostgreSQL, and Docker
applications.

Use this guide when you want to turn the starter kit into a named product. Use `AGENTS.md` as the
assistant operating guide and `docs/ai/new_app_bootstrap_checklist.md` as the detailed checklist.

## Recommended Flow

1. Create a new repository or branch from this starter kit.
1. Decide the app identity values before renaming files.
1. Preview the bootstrap changes.
1. Apply the bootstrap changes only after reviewing the preview.
1. Validate backend, frontend, Docker Compose, and hooks.
1. Start building the first real feature using the project playbooks and scaffolds.

## Minimum App Identity

Decide these values first:

- Application name, for example `Example Portal`.
- Short product description.
- Internal slug, for example `example-portal`.
- Initial user roles and permissions.
- Initial routes or screens.
- Initial data entities.
- Integrations that are in scope now.
- Integrations explicitly out of scope.
- Deployment target or local-only expectation.

When these are not clear, fill `docs/ai/templates/new_app_request.md` and give it to the assistant.

## Preview Identity Changes

Run from the repository root:

```powershell
python scripts/bootstrap_new_app.py --app-name "Example Portal" --description "A portal for example workflows."
```

The script runs in dry-run mode by default. It prints the identity values it derived and the files it
would update.

Use explicit overrides when defaults are not right:

```powershell
python scripts/bootstrap_new_app.py `
  --app-name "Example Portal" `
  --slug example-portal `
  --description "A portal for example workflows." `
  --db-name example_main `
  --jwt-issuer example-portal `
  --jwt-audience example-portal-api
```

## Apply Identity Changes

After reviewing the preview, rerun the command with `--write`:

```powershell
python scripts/bootstrap_new_app.py `
  --app-name "Example Portal" `
  --slug example-portal `
  --description "A portal for example workflows." `
  --db-name example_main `
  --jwt-issuer example-portal `
  --jwt-audience example-portal-api `
  --write
```

The script intentionally changes identity surfaces only. It does not design product features, change
auth behavior, add routes, alter permissions, create migrations, or add integrations.

## Review Generated Changes

Review the changed files before continuing:

```powershell
git diff
```

Commonly changed files include:

- `README.md`
- `backend/README.md`
- `.env_examples`
- `compose.yaml`
- `compose.test.yaml`
- `compose.prod.yaml`
- `backend/app/core/config/settings.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/index.html`
- `frontend/src/shared/i18n/ui-text.ts`

## Validate the Bootstrapped App

Run the gates that prove the renamed foundation still works:

```powershell
docker compose config
docker compose -f compose.test.yaml config
docker compose -f compose.yaml -f compose.prod.yaml config
python -m pytest backend/tests
python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100
npm --prefix frontend run check
npm --prefix frontend run test:e2e:ci
npm --prefix frontend run build
pre-commit run --all-files
```

If route, auth, RBAC, API, runtime, or feature behavior changes during bootstrap, update the affected
backend and frontend operation docs in the same change.

## Run the App

Create `.env` from `.env_examples` after bootstrap:

```powershell
Copy-Item .env_examples .env
```

Start the stack:

```powershell
docker compose up --build
```

Open:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

Seed an admin account when needed by following `backend/README.md`.

## Build the First Feature

For a new full-stack feature, preview the scaffold first:

```powershell
python scripts/scaffold_feature.py --dry-run full-stack <feature-name> --route /your-route --with-model
```

Then implement the feature using:

- `AGENTS.md`
- `backend/docs/backend_playbook.md`
- `frontend/docs/frontend_playbook.md`
- affected operation docs under `backend/docs/operations/` and `frontend/docs/operations/`
- `docs/ai/templates/full_stack_feature_request.md` when scope needs structure
