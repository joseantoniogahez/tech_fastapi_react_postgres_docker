# Frontend Code Change Request Template

## How to Use This Template With the AI Assistant

1. Describe exactly what should change and what must stay stable.
1. Reference the rules/contracts the AI must follow.
1. List required tests and quality gates.
1. Paste the completed template in your request to the assistant.

## Problem and Goal

Describe what must change and what outcome is expected.

## Scope (In / Out)

### In Scope

- List exact files/modules/behaviors to change.

### Out of Scope

- List what must stay unchanged.

## API, Auth, Routing, and State Implications

- API behavior impact.
- Auth/session impact.
- Routing/navigation impact.
- Query/cache/state impact.

## UX, Accessibility, and Error Handling

- UX changes and fallback behavior.
- Accessibility impact.
- Error handling updates.

## Acceptance Criteria

- Define objective acceptance conditions.

## AI Execution Constraints (Required)

- Docs the AI must read before coding (minimum):
  - `frontend/docs/frontend_playbook.md`
  - Relevant files in `frontend/docs/operations/`
- Mandatory implementation constraints:
  - Keep feature/shared boundaries.
  - Preserve explicit routing/auth/error contracts unless this request says otherwise.
  - Keep user-facing copy sourced from `src/shared/i18n/ui-text.ts`.
- Expected AI output:
  - Implement only in-scope changes.
  - Add/update tests and docs as required.
  - Report executed validation commands and outcomes.

## Required Tests and Validation

- Tests to add/update.
- Contract tests to add/update when rules/docs/API contracts change.
- Commands to run:
  - `npm --prefix frontend run check`
  - `npm --prefix frontend run test:e2e:ci` (required when auth/routing/error behavior changes)
  - `npm --prefix frontend run build`
  - `.\.venv\Scripts\pre-commit.exe run --all-files`

## Reviewer Validation Checklist

- [ ] Change is scoped and justified.
- [ ] Contract impacts are explicit.
- [ ] AI constraints are explicit enough to reproduce the same result.
- [ ] Tests and validation commands are complete.
- [ ] Documentation/foundation status updates are included when required.
