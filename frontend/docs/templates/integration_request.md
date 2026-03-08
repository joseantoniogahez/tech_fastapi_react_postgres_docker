# Frontend Integration Request Template

## How to Use This Template With the AI Assistant

1. Fill every section with concrete integration details.
1. Reference the exact docs/contracts the AI must honor.
1. Define deterministic failure behavior and validation commands.
1. Paste the completed template in your request to the assistant.

## Problem and Goal

Describe the integration need and the expected frontend behavior.

## Scope (In / Out)

### In Scope

- List integration-related frontend behaviors.

### Out of Scope

- List explicit non-goals.

## API, Auth, Routing, and State Implications

- API request/response shape changes.
- Auth/session impact (token usage, unauthorized handling).
- Routing impact (guards, redirects, route errors).
- Query/cache/state behavior changes.

## UX, Accessibility, and Error Handling

- Loading and failure UX.
- Accessibility checks for new states.
- Observability/error requirements (request-id, diagnostics).

## Acceptance Criteria

- Define expected success and failure outcomes.

## AI Execution Constraints (Required)

- Docs the AI must read before coding (minimum):
  - `frontend/docs/frontend_playbook.md`
  - `frontend/docs/operations/api_consumer_matrix.md`
  - `frontend/docs/operations/api_contract_sync.md`
  - Any additional impacted operation contract document(s)
- Integration boundaries that must be preserved:
  - List modules/abstractions that must remain unchanged.
- Expected AI output:
  - Implement integration behavior and error handling.
  - Add/update tests for success and failure paths.
  - Update impacted contracts/docs.
  - Report executed validation commands and outcomes.

## Required Tests and Validation

- Integration-flow tests required.
- Failure-path tests required.
- Contract tests required when API/docs contracts change.
- Commands to run:
  - `npm --prefix frontend run check`
  - `npm --prefix frontend run test:e2e:ci` (required when integration changes auth/routing/error journeys)
  - `npm --prefix frontend run build`

## Reviewer Validation Checklist

- [ ] Integration boundaries are clear and maintainable.
- [ ] Failure handling is deterministic.
- [ ] Observability/error behavior is documented.
- [ ] AI execution constraints are explicit and enforceable.
- [ ] Validation coverage is sufficient.
