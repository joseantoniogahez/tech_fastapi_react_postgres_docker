# Feature Request Template

## How to Use This Template With the AI Assistant

1. Fill every section with concrete details (no placeholders).
1. Reference backend docs/contracts the assistant must follow.
1. Define hard scope boundaries and required validations.
1. Paste the completed template in your request to the assistant.

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

## AI Execution Constraints (Required)

- Docs the AI must read before coding (minimum):
  - `backend/docs/backend_playbook.md`
  - Relevant files in `backend/docs/operations/`
  - Relevant files in `backend/docs/architecture/` when architecture is impacted
- Allowed files/modules to change:
  - List explicit paths.
- Protected files/modules that must not change:
  - List explicit paths.
- Expected AI output:
  - Implement behavior changes.
  - Add/update tests.
  - Update impacted contracts/docs.
  - Report executed validation commands and outcomes.

## Required Tests

- Router tests
- Service tests
- Repository tests (if persistence changes)
- Documentation contract tests (if docs change)

## Reviewer Validation Checklist

- [ ] Request aligns with `backend/docs/backend_playbook.md`.
- [ ] Public endpoint contract impact is explicit.
- [ ] Permission and scope impact is explicit.
- [ ] AI execution constraints are explicit and enforceable.
- [ ] Test expectations are specific and complete.
