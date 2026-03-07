# Feature Request Template

## Problem and Goal

Describe the user or business problem and the concrete backend goal.

## Scope (In / Out)

### In Scope

- List exact behaviors to add or change.

### Out of Scope

- List explicit exclusions to prevent scope drift.

## API, Data, and Authorization Implications

- API endpoints to add or change.
- Request/response contract changes.
- Data model or migration changes.
- New or changed permissions and required scopes.

## Observability and Error Handling

- Logs/events required for traceability.
- Expected domain errors and HTTP mapping updates.

## Acceptance Criteria

- Describe measurable pass/fail outcomes.

## Required Tests

- Router tests
- Service tests
- Repository tests (if persistence changes)
- Documentation contract tests (if docs change)

## Reviewer Validation Checklist

- [ ] Request aligns with `backend/docs/backend_playbook.md`.
- [ ] Public endpoint contract impact is explicit.
- [ ] Permission and scope impact is explicit.
- [ ] Test expectations are specific and complete.
