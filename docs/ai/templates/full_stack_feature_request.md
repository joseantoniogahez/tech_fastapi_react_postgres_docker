# Full-Stack Feature Request Template

## How to Use This Template With the AI Assistant

1. Fill every section with concrete details.
1. Reference exact backend and frontend contracts the assistant must follow.
1. Define hard scope boundaries, protected files, and required validation commands.
1. Paste the completed template in your request to the assistant.

## Problem and Goal

Describe the user or business problem and the concrete full-stack outcome.

## Scope

### In Scope

- List exact backend behaviors to add or change.
- List exact frontend behaviors to add or change.
- List docs, tests, migrations, OpenAPI sync, or operational updates expected.

### Out of Scope

- List explicit exclusions to prevent scope drift.
- List deferred features, integrations, roles, screens, or data fields.

## Backend Impact

- API endpoints to add or change.
- Request and response contract changes.
- Data model, repository, service, or migration changes.
- Auth, current-user, permission, role, or scope changes.
- Domain errors and HTTP status mapping changes.
- Observability, outbox, or integration-port behavior.

## Frontend Impact

- Routes, navigation, route guards, or access-policy changes.
- Pages, components, shared modules, or user-facing text changes.
- API consumers, generated OpenAPI artifact, or error handling changes.
- Query, mutation, cache invalidation, or session behavior changes.
- Loading, empty, unauthorized, validation, and recovery states.
- Accessibility, e2e smoke, observability, runtime config, or performance implications.

## UX and Product Expectations

- Primary user journey.
- Success states.
- Empty states.
- Error and recovery states.
- Accessibility expectations.
- Responsive behavior expectations.

## Acceptance Criteria

- Describe measurable pass/fail outcomes for backend behavior.
- Describe measurable pass/fail outcomes for frontend behavior.
- Describe required docs and contract updates.
- Describe required validation commands and expected results.

## AI Execution Constraints

Required docs to read before coding:

- `AGENTS.md`
- `backend/docs/backend_playbook.md`
- `backend/docs/foundation_status.md`
- Relevant backend files in `backend/docs/operations/`
- Relevant backend files in `backend/docs/architecture/`
- `frontend/docs/frontend_playbook.md`
- `frontend/docs/foundation_status.md`
- Relevant frontend files in `frontend/docs/operations/`

Allowed files or modules to change:

- List exact paths or folders.

Protected files or modules that must not change:

- List exact paths or folders.

Expected AI output:

- Implement the backend behavior.
- Implement the frontend behavior.
- Add or update tests.
- Update impacted docs and contract inventories.
- Sync or check OpenAPI artifacts.
- Report validation commands and outcomes.

## Required Tests and Validation

Backend tests:

- Router tests.
- Service tests.
- Repository tests when persistence changes.
- Permission or authorization tests when RBAC changes.
- Documentation contract tests when docs or public contracts change.

Frontend tests:

- Page or component tests.
- Route guard tests when routing or auth changes.
- API consumer tests when API behavior changes.
- Query or mutation policy tests when state behavior changes.
- Accessibility route baseline tests when routes or states change.
- E2E smoke tests when auth, routing, or error journeys change.

Commands to run:

- `python -m pytest backend/tests`
- `python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`
- `npm --prefix frontend run openapi:sync` when backend OpenAPI output changes.
- `npm --prefix frontend run openapi:check` when backend OpenAPI output should be unchanged.
- `npm --prefix frontend run check`
- `npm --prefix frontend run test:e2e:ci` when auth, routing, or error journeys change.
- `npm --prefix frontend run build`
- `pre-commit run --all-files` when docs, hooks, formatting, Docker, or shared config changed.

## Reviewer Validation Checklist

- [ ] Scope and exclusions are explicit.
- [ ] Backend API, data, auth, RBAC, error, and docs impact are explicit.
- [ ] Frontend route, state, UX, accessibility, and docs impact are explicit.
- [ ] Acceptance criteria are measurable.
- [ ] Allowed and protected files are enforceable.
- [ ] OpenAPI sync or check expectation is explicit.
- [ ] Required tests match the changed behavior.
- [ ] Validation commands are complete for the change.
