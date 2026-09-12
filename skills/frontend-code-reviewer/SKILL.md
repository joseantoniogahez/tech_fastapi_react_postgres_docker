---
name: frontend-code-reviewer
description: Review React frontend changes for correctness, accessibility, security, regressions, API and route drift, missing tests, and validation gaps. Use when a review touches routes, pages, shared UI, API consumers, auth or RBAC screens, query flows, runtime config, observability, e2e, performance, or frontend documentation.
---

# Frontend Code Reviewer

## Workflow

1. Read `AGENTS.md`, `frontend/docs/frontend_playbook.md`, and
   `frontend/docs/foundation_status.md`.
1. Inspect changed files and nearby code, then read only affected operation documents.
1. Trace each screen from route and access guard through API consumer, contract parser, query or
   mutation behavior, and rendered states.
1. Compare behavior with route, API consumer, OpenAPI, mutation, runtime, security, observability,
   accessibility, e2e, and performance contracts.
1. Read product docs only when a derived application explicitly declares them canonical.
1. Inspect focused tests and run the smallest checks needed to prove or disprove findings.
1. Report findings first by severity with file and line references. Do not modify code unless the
   user also requests fixes.

## Review Gates

- Preserve `app -> features -> shared` dependency direction and centralized route composition.
- Confirm route access, navigation visibility, and direct navigation agree.
- Confirm API calls use shared HTTP/error handling, validate responses, and match backend OpenAPI.
- Confirm retry and invalidation cannot duplicate writes or leave stale views.
- Confirm loading, empty, error, unauthorized, disabled, and success states are accessible.
- Confirm diagnostics are redaction-safe and runtime failures remain observable.
- Confirm relevant component, contract, accessibility, e2e, and performance coverage moves with
  behavior.

## Validation And Output

Use the frontend gates in `AGENTS.md`. Output findings, questions, validation and gaps, then a
concise summary. If there are no findings, say so and name remaining risk.
