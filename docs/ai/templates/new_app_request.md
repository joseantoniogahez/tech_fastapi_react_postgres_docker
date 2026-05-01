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
- AI-governance plan changes:
- Foundation status changes:

## AI Execution Constraints

Required docs to read before coding:

- `AGENTS.md`
- `AI_GOVERNED_STARTER_KIT_PLAN.md`
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

- `python scripts/bootstrap_new_app.py --app-name "<App Name>" --description "<Description>"`

Recommended apply command after reviewing the preview:

- `python scripts/bootstrap_new_app.py --app-name "<App Name>" --description "<Description>" --write`

Commands to run after in-place bootstrap work:

- Docker Compose config validation for affected profiles.
- `python -m pytest backend/tests`
- `python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`
- `npm --prefix frontend run check`
- `npm --prefix frontend run test:e2e:ci` when route, auth, or error journeys change.
- `npm --prefix frontend run build`
- `pre-commit run --all-files`

## Reviewer Validation Checklist

- [ ] App identity is explicit and consistently applied.
- [ ] Bootstrap mode is explicit.
- [ ] Compose names, database name, JWT issuer, and JWT audience are addressed.
- [ ] Backend auth, RBAC, seed, data, and API expectations are explicit.
- [ ] Frontend routes, visible text, navigation, and config expectations are explicit.
- [ ] Integrations are clearly in scope or out of scope.
- [ ] Allowed and protected files are enforceable.
- [ ] Validation commands are complete for the requested bootstrap mode.
