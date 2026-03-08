# Code Change Request Template

## How to Use This Template With the AI Assistant

1. Fill every section with exact scope and constraints.
1. Reference backend playbook/contracts the assistant must follow.
1. Define mandatory tests and validation commands.
1. Paste the completed template in your request to the assistant.

## Problem and Goal

Describe what is wrong or missing today and what the backend should do after the change.

## Scope (In / Out)

### In Scope

- List exact modules/behaviors to change.

### Out of Scope

- List what must remain untouched.

## API, Data, and Authorization Implications

- Public API changes (if any).
- Data model/migration implications (if any).
- Authorization and permission implications (if any).

## Observability and Error Handling

- Logging/telemetry additions or updates.
- Error behavior and mapping expectations.

## Acceptance Criteria

- Define expected behavior with verifiable conditions.

## AI Execution Constraints (Required)

- Docs the AI must read before coding (minimum):
  - `backend/docs/backend_playbook.md`
  - Relevant files in `backend/docs/operations/`
  - Relevant files in `backend/docs/architecture/` when applicable
- Mandatory implementation constraints:
  - Keep router/service/repository boundaries.
  - Keep DI/UoW behavior intact unless explicitly requested otherwise.
  - Preserve normalized error mapping unless explicitly requested otherwise.
- Expected AI output:
  - Implement only in-scope changes.
  - Add/update tests and docs as required.
  - Report executed validation commands and outcomes.

## Required Tests

- Existing tests to update.
- New tests required.
- Documentation contracts to update and validate.

## Reviewer Validation Checklist

- [ ] Request references affected contracts and docs.
- [ ] Scope boundaries are explicit and realistic.
- [ ] Acceptance criteria are testable.
- [ ] AI execution constraints are explicit and reproducible.
- [ ] Test expectations are complete for changed behavior.
