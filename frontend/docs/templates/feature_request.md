# Frontend Feature Request Template

## How to Use This Template With the AI Assistant

1. Fill every section with concrete details (avoid placeholders like `TBD`).
1. Reference the exact frontend contracts/playbook the assistant must follow.
1. State which files may change and which files are out of scope.
1. Paste the completed template in your request to the assistant.

## Problem and Goal

Describe the product or user problem and the expected frontend outcome.

## Scope (In / Out)

### In Scope

- List exact frontend behaviors to add or change.

### Out of Scope

- List explicit exclusions.

## API, Auth, Routing, and State Implications

- API endpoints/contracts affected.
- Auth/session implications.
- Routing/navigation implications.
- Query/cache/state implications.

## UX, Accessibility, and Error Handling

- UX expectations and failure states.
- Accessibility impact and required checks.
- Error messaging and recovery behavior.

## Acceptance Criteria

- Define measurable pass/fail criteria.

## AI Execution Constraints (Required)

- Docs the AI must read before coding (minimum):
  - `frontend/docs/frontend_playbook.md`
  - Relevant files in `frontend/docs/operations/`
- Allowed files/modules to change:
  - List explicit paths or folders.
- Protected files/modules that must not change:
  - List explicit paths or folders.
- Expected AI output:
  - Implement the behavior.
  - Add/update tests.
  - Update impacted docs/contracts.
  - Report executed validation commands and outcomes.

## Required Tests and Validation

- Unit/integration tests required.
- Contract tests required (if applicable).
- E2E smoke tests required when auth/routing/error behavior changes.
- Commands to run:
  - `npm --prefix frontend run check`
  - `npm --prefix frontend run test:e2e:ci` (required for auth/routing/error flow changes)
  - `npm --prefix frontend run build`

## Reviewer Validation Checklist

- [ ] Scope and goal are explicit.
- [ ] API/auth/routing/state impact is explicit.
- [ ] Acceptance criteria are testable.
- [ ] AI execution constraints list exact docs, scope limits, and validation expectations.
- [ ] Validation commands are complete.
