# New App Request Template

## How to Use This Template With the AI Assistant

1. Fill every section with concrete details before asking the assistant to bootstrap a new app.
1. Decide whether the work should rename this repository in place or prepare a reusable checklist.
1. Define protected files and validation commands before broad rename work begins.
1. Paste the completed template in your request to the assistant.

## App Identity

- Application name:
- Short product description:
- Domain or industry:
- Primary user types:
- Internal project slug:
- Public product name:
- Repository/package naming expectations:

## Starting Template Snapshot

- Credential-free HTTP(S) template repository URL:
- Immutable commit or reviewed tag:
- Resolved full commit (must equal checkout HEAD):
- Resolved tree:
- Compatibility review for a newer snapshot:
- Confirmation that checkout is pristine and Git-clean:
- Filesystem/mount confirmation for same-directory hardlinks and same-filesystem replacement:
- Required explicit per-file Windows DACLs, if any (handled outside identity bootstrap):

## Bootstrap Mode

Choose one:

- Rename this repository in place.
- Create a plan only.
- Create a branch-ready checklist and leave code unchanged.
- Prepare a new-app scaffold workflow for later execution.

## Product Foundation

- Main user problem:
- Initial user journeys:
- Initial routes or screens:
- Initial backend capabilities:
- Initial data entities:
- Initial roles:
- Initial permissions:
- Initial admin workflows:

## Branding and Terminology

- Preferred product terminology:
- Terms to avoid:
- Initial visible app name:
- Login/register/welcome/profile wording expectations:
- Admin area naming expectations:
- Color, typography, or visual direction if already known:

## Runtime and Environment Changes

- Docker Compose project names:
- Database name:
- API title or description:
- JWT issuer:
- JWT audience:
- Frontend package name:
- Environment variable changes:
- Local development URL expectations:
- Production deployment assumptions:

## Backend Expectations

- Auth and registration policy:
- RBAC baseline:
- Seed or bootstrap admin expectations:
- Data model changes:
- API namespace expectations:
- Integration ports needed now:
- Integration providers explicitly out of scope:
- Migration expectations:

## Frontend Expectations

- Public routes:
- Authenticated routes:
- Admin routes:
- Navigation expectations:
- API consumer changes:
- Runtime config changes:
- User-facing text changes:
- Accessibility expectations:
- E2E smoke expectations:

## Documentation Expectations

- Root README changes:
- Backend README or docs changes:
- Frontend README or docs changes:
- `AGENTS.md` changes:
- AI governance docs changes:
- Foundation status changes:

## AI Execution Constraints

Required docs to read before coding:

- `AGENTS.md`
- `docs/ai/start_new_project.md`
- `docs/ai/new_app_bootstrap_checklist.md`
- `README.md`
- `backend/README.md`
- `frontend/README.md`
- `backend/docs/backend_playbook.md`
- `frontend/docs/frontend_playbook.md`
- Relevant backend and frontend operation docs.

Allowed files or modules to change:

- List exact paths or folders.

Protected files or modules that must not change:

- List exact paths or folders.

Expected AI output:

- Confirm bootstrap mode and assumptions.
- Apply requested app identity changes.
- Update affected backend, frontend, Docker, env, README, docs, and tests.
- Preserve existing architecture and validation gates.
- Report validation commands and outcomes.

## Required Tests and Validation

Recommended preview command before in-place bootstrap:

- `.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "<https-repository>" --source-revision "<commit-or-tag>" --app-name "<App Name>" --description "<Description>"`

Recommended apply command after reviewing the preview:

- `.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "<https-repository>" --source-revision "<commit-or-tag>" --app-name "<App Name>" --description "<Description>" --write`

Commands to run after in-place bootstrap work:

- `docker compose --env-file .env_examples -f compose.yaml config -q`
- `docker compose --env-file .env_examples -f compose.yaml -f compose.override.yaml config -q`
- `docker compose --env-file .env_examples -f compose.test.yaml config -q`
- `docker compose --env-file .env_examples -f compose.yaml -f compose.test.yaml config -q`
- `docker compose --env-file .env_examples -f compose.yaml -f compose.prod.yaml config -q`
- `.\.venv\Scripts\python.exe -m pytest backend/tests`
- `.\.venv\Scripts\python.exe -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`
- `npm --prefix frontend run check`
- `npm --prefix frontend run test:e2e:ci`
- `npm --prefix frontend run build`
- `.\.venv\Scripts\python.exe -m pre_commit run --all-files`

## Reviewer Validation Checklist

- [ ] App identity is explicit and consistently applied.
- [ ] Source repository, revision, full commit/tree, clean checkout, and generated provenance are explicit.
- [ ] Filesystem hardlink/replacement support and any custom Windows DACL migration are explicit.
- [ ] Bootstrap mode is explicit.
- [ ] Compose names, database name, JWT issuer, and JWT audience are addressed.
- [ ] Backend auth, RBAC, seed, data, and API expectations are explicit.
- [ ] Frontend routes, visible text, navigation, and config expectations are explicit.
- [ ] Integrations are clearly in scope or out of scope.
- [ ] Allowed and protected files are enforceable.
- [ ] Validation commands are complete for the requested bootstrap mode.
