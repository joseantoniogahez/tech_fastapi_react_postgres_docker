# New App Bootstrap Checklist

Use this checklist when turning this starter kit into a new application. Start from
`docs/ai/templates/new_app_request.md` and keep `AGENTS.md` as the operating guide.

## Before Changing Files

- [ ] Confirm bootstrap mode: plan only, in-place rename, or scaffold workflow.
- [ ] Confirm application name, public product name, and internal slug.
- [ ] Confirm product description and landing-page positioning.
- [ ] Confirm initial user types, roles, permissions, and admin workflows.
- [ ] Confirm initial routes, backend capabilities, and data entities.
- [ ] Confirm integrations that are in scope and explicitly out of scope.
- [ ] Confirm deployment expectations and local development ports.
- [ ] Confirm allowed files and protected files.

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
python scripts/bootstrap_new_app.py --app-name "Example Portal" --description "A portal for example workflows."
```

Apply only after reviewing the preview:

```powershell
python scripts/bootstrap_new_app.py --app-name "Example Portal" --description "A portal for example workflows." --write
```

Use explicit overrides when defaults are not right:

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

## Validation After In-Place Bootstrap

- [ ] Validate Docker Compose config for affected profiles.
- [ ] Run `python -m pytest backend/tests`.
- [ ] Run `python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`.
- [ ] Run `npm --prefix frontend run check`.
- [ ] Run `npm --prefix frontend run test:e2e:ci` when route, auth, or error journeys change.
- [ ] Run `npm --prefix frontend run build`.
- [ ] Run `pre-commit run --all-files`.

## Reviewer Checks

- [ ] App identity is consistent across Compose, env examples, backend JWT defaults, frontend package
  metadata, README text, and visible UI text.
- [ ] JWT issuer and audience are not left as `fastapi-template` defaults.
- [ ] Compose project names are isolated from the starter kit defaults.
- [ ] Database and container hostnames are clear and environment-specific.
- [ ] No feature behavior changed unintentionally during rename work.
- [ ] Documentation describes the new app without losing operational instructions.
