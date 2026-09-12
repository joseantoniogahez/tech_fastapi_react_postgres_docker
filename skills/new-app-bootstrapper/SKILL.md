---
name: new-app-bootstrapper
description: New application bootstrap workflow for this FastAPI, React, PostgreSQL, and Docker starter kit. Use when Codex must turn the starter kit into a named product, preview or apply identity changes, update Compose/env/JWT/package/README/UI naming surfaces, preserve behavior during identity-only bootstrap, or guide a user through the new-app request template and validation gates.
---

# New App Bootstrapper

## Overview

Bootstrap this starter kit into a named application while keeping identity changes separate from
feature design. Use the dry-run-first script flow and keep canonical docs as the source of truth.

Operate only on a pristine, compatible starter-kit snapshot. If identity was already customized or
the snapshot cannot be matched to this template, stop and request an explicit migration plan.

## Required Reading

Read in this order:

1. `AGENTS.md`
1. `docs/ai/start_new_project.md`
1. `docs/ai/new_app_bootstrap_checklist.md`
1. `docs/ai/template_reuse_contract.md`
1. `docs/ai/templates/new_app_request.md` when app identity or scope is incomplete
1. `README.md`
1. `backend/README.md`
1. `frontend/README.md`

Read backend or frontend playbooks only when bootstrap scope includes behavior changes beyond
identity surfaces.

## Scope Rules

Identity-only bootstrap may update:

- root and service README text,
- `.env_examples`,
- Docker Compose project names and service hostnames,
- database name,
- backend JWT issuer and audience defaults,
- frontend package metadata and lockfile root name,
- frontend document title and visible starter text.

Identity-only bootstrap must not:

- add product features,
- change API behavior,
- add routes,
- alter permissions or RBAC semantics,
- create migrations,
- add integrations,
- change validation gates.

If the user wants those changes, split the work into a follow-up feature request.

## Workflow

1. Confirm bootstrap mode: plan only, dry-run preview, or in-place apply.
1. Confirm the credential-free source repository URL and either a full 40-character commit or an
   existing reviewed tag, and require that it resolve to the clean checkout's exact `HEAD`. Reject
   mutable branches and symbolic revisions.
1. Confirm app identity values:
   - application name,
   - short description,
   - internal slug,
   - frontend package name if different from default,
   - Compose project names if different from defaults,
   - database name,
   - JWT issuer and audience,
   - visible frontend naming.
1. Confirm initial roles, routes, data entities, integrations, deployment expectations, allowed
   files, and protected files when the user asks for more than identity-only bootstrap.
1. If identity details are incomplete, ask a concise question or use
   `docs/ai/templates/new_app_request.md`.
1. Reject an existing provenance artifact or incompatible/dirty snapshot; identity changes to an
   existing application use a separate migration procedure.
1. Confirm that the repository/targets use a compatible same-filesystem layout with hardlink and
   same-filesystem replacement support. Route required explicit per-file Windows DACLs to a separate
   reviewed procedure; bootstrap applies the destination directory's inherited ACL.
1. Run `scripts/bootstrap_new_app.py` without `--write` first.
1. Review the dry-run output with the user-facing assumptions.
1. Apply with `--write` only when the requested scope is clear.
1. If automatic rollback reports incomplete recovery, or the process/host terminated abruptly, stop,
   retain `.bootstrap-*` plus any reported adjacent `.bootstrap-install-*` file, and review every
   target and backup; do not rerun bootstrap or delete recovery data.
1. Verify generated `docs/ai/template_provenance.json`; never remove it to force a second run.
1. Review `git diff` for identity consistency.
1. Update docs in the same change when runtime behavior or validation rules change.
1. Run matching validation gates.

## Script Usage

Preview:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows."
```

POSIX: replace `.\.venv\Scripts\python.exe` with `./.venv/bin/python`.

Apply after preview:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows." --write
```

Use explicit overrides when defaults are not correct:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py `
  --source-repository "https://github.com/example/foundation" `
  --source-revision "<commit-or-tag>" `
  --app-name "Example Portal" `
  --slug example-portal `
  --description "A portal for example workflows." `
  --db-name example_main `
  --jwt-issuer example-portal `
  --jwt-audience example-portal-api `
  --write
```

## Validation

For identity-only bootstrap, run:

- `docker compose --env-file .env_examples -f compose.yaml config -q`
- `docker compose --env-file .env_examples -f compose.yaml -f compose.override.yaml config -q`
- `docker compose --env-file .env_examples -f compose.test.yaml config -q`
- `docker compose --env-file .env_examples -f compose.yaml -f compose.test.yaml config -q`
- `docker compose --env-file .env_examples -f compose.yaml -f compose.prod.yaml config -q`
- `.\.venv\Scripts\python.exe -m pytest backend\tests` (PowerShell)
- `./.venv/bin/python -m pytest backend/tests` (POSIX)
- `.\.venv\Scripts\python.exe -m pytest backend\tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`
- `npm --prefix frontend run check`
- `npm --prefix frontend run test:e2e:ci`
- `npm --prefix frontend run build`
- `.\.venv\Scripts\python.exe -m pre_commit run --all-files` (PowerShell; use
  `./.venv/bin/python` on POSIX)

## Final Report

Report:

- bootstrap mode used,
- app identity values applied,
- source repository, requested revision, resolved full commit/tree, and provenance path,
- files changed,
- whether changes were identity-only or included behavior changes,
- validation commands run and outcomes,
- commands skipped and why,
- residual risk or follow-up feature work.
