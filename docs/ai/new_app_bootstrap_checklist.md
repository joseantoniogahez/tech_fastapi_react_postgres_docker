# New App Bootstrap Checklist

Use this checklist when turning this starter kit into a new application. Start from
`docs/ai/start_new_project.md`; when app identity or scope is still unclear, fill
`docs/ai/templates/new_app_request.md`. Keep `AGENTS.md` as the operating guide.

## Before Changing Files

- [ ] Confirm bootstrap mode: plan only, in-place rename, or scaffold workflow.
- [ ] Confirm application name, public product name, and internal slug.
- [ ] Confirm product description and landing-page positioning.
- [ ] Confirm initial user types, roles, permissions, and admin workflows.
- [ ] Confirm initial routes, backend capabilities, and data entities.
- [ ] Confirm integrations that are in scope and explicitly out of scope.
- [ ] Confirm deployment expectations and local development ports.
- [ ] Confirm allowed files and protected files.
- [ ] Record the credential-free template repository URL and either a full 40-character commit or
  an existing reviewed tag; do not use a mutable branch or symbolic revision.
- [ ] Confirm the revision resolves to the checkout's full `HEAD` commit and capture its tree.
- [ ] Confirm Git status is clean and no `docs/ai/template_provenance.json` exists.

## Identity Values to Decide

- [ ] App title.
- [ ] App slug, using lowercase letters, digits, and hyphens.
- [ ] Environment prefix, using lowercase letters, digits, and underscores.
- [ ] Frontend package name.
- [ ] Docker Compose project names for dev, test, and prod.
- [ ] Database name.
- [ ] API hostname.
- [ ] Database hostname.
- [ ] Frontend hostname.
- [ ] JWT issuer.
- [ ] JWT audience.
- [ ] Browser document title.
- [ ] Landing page title, subtitle, badge, and loading text.

## Files Usually Touched

- [ ] `README.md`
- [ ] `backend/README.md`
- [ ] `frontend/README.md`
- [ ] `.env_examples`
- [ ] `compose.yaml`
- [ ] `compose.test.yaml`
- [ ] `compose.prod.yaml`
- [ ] `backend/app/core/config/settings.py`
- [ ] `frontend/package.json`
- [ ] `frontend/package-lock.json`
- [ ] `frontend/index.html`
- [ ] `frontend/src/shared/i18n/ui-text.ts`
- [ ] Relevant docs under `backend/docs/` and `frontend/docs/` when behavior changes.

## Recommended Script Flow

Preview changes first:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows."
```

Apply only after reviewing the preview:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows." --write
```

Use explicit overrides when defaults are not right:

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

## Validation After In-Place Bootstrap

- [ ] Run `docker compose --env-file .env_examples -f compose.yaml config -q`.
- [ ] Run `docker compose --env-file .env_examples -f compose.yaml -f compose.override.yaml config -q`.
- [ ] Run `docker compose --env-file .env_examples -f compose.test.yaml config -q`.
- [ ] Run `docker compose --env-file .env_examples -f compose.yaml -f compose.test.yaml config -q`.
- [ ] Run `docker compose --env-file .env_examples -f compose.yaml -f compose.prod.yaml config -q`.
- [ ] Confirm `docs/ai/template_provenance.json` contains the resolved source commit/tree and derived identity.
- [ ] Confirm a second bootstrap attempt is rejected; do not delete provenance to rerun it.
- [ ] Confirm normal success and injected recoverable failures leave no `.bootstrap-*` transaction.
- [ ] Confirm generated replacements retain the prior POSIX mode where applicable and receive the
  destination directory's normal inherited ACL on Windows.
- [ ] Confirm the checkout filesystem supports same-directory hardlinks; explicit per-file Windows
  DACLs are outside bootstrap preservation and require a separate reviewed procedure.
- [ ] If rollback is reported incomplete, retain its `.bootstrap-*` backups and stop for manual
  recovery; do not rerun bootstrap.
- [ ] After `SIGKILL`, power loss, or other uncatchable termination, treat the checkout as partial and
  inspect retained transaction/adjacent install artifacts before continuing.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest backend/tests`.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`.
- [ ] Run `npm --prefix frontend run check`.
- [ ] Run `npm --prefix frontend run test:e2e:ci`.
- [ ] Run `npm --prefix frontend run build`.
- [ ] Run `.\.venv\Scripts\python.exe -m pre_commit run --all-files`.

## Reviewer Checks

- [ ] App identity is consistent across Compose, env examples, backend JWT defaults, frontend package
  metadata, README text, and visible UI text.
- [ ] JWT issuer and audience are not left as `fastapi-template` defaults.
- [ ] Compose project names are isolated from the starter kit defaults.
- [ ] Database and container hostnames are clear and environment-specific.
- [ ] No feature behavior changed unintentionally during rename work.
- [ ] Documentation describes the new app without losing operational instructions.
- [ ] Provenance remains committed and states that the application is not the pristine template.
