# Integration Request Template

## How to Use This Template With the AI Assistant

1. Fill every section with concrete integration behavior and failure expectations.
1. Reference backend architecture and operation docs the assistant must respect.
1. Define test coverage and validation commands up front.
1. Paste the completed template in your request to the assistant.

## Problem and Goal

Describe the integration need, target system, and expected backend outcome.

## Scope (In / Out)

### In Scope

- List integration behaviors to implement.

### Out of Scope

- List explicit non-goals.

## API, Data, and Authorization Implications

- API endpoints affected by the integration.
- Data contracts/payload shapes affected.
- Persistence side effects and transaction boundaries.
- Authorization implications for callers.

## Observability and Error Handling

- Required structured logs/events.
- Retry, timeout, and failure behavior.
- Domain error mapping changes, if any.

## Acceptance Criteria

- Define integration success behavior and expected failure behavior.

## AI Execution Constraints (Required)

- Docs the AI must read before coding (minimum):
  - `backend/docs/backend_playbook.md`
  - Relevant files in `backend/docs/operations/`
  - `backend/docs/architecture/clean_architecture_ports_adapters.md`
  - `backend/docs/architecture/dependency_injection.md`
- Mandatory boundaries:
  - Keep ports/adapters boundaries intact.
  - Keep transaction handling in UnitOfWork for write side effects.
  - Keep normalized error contracts.
- Expected AI output:
  - Implement integration behavior and deterministic failure handling.
  - Add/update tests for success and failure paths.
  - Update impacted docs/contracts.
  - Report executed validation commands and outcomes.

## Required Tests

- Service-level integration orchestration tests.
- Failure-path tests (timeouts, invalid payloads, unavailable dependency).
- Router and authorization tests when external calls affect public behavior.
- Documentation contract tests if docs are updated.

## Reviewer Validation Checklist

- [ ] Integration boundaries follow ports/adapters design.
- [ ] Failure behavior is deterministic and test-covered.
- [ ] Observability events are defined.
- [ ] Public contract and permission impact is documented.
- [ ] AI execution constraints are explicit and enforceable.
