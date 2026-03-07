# Integration Request Template

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
