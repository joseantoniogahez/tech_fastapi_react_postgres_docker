<!--
name: frontend-feature-builder
description: Frontend feature delivery for this Vite, React, TypeScript, React Router, TanStack Query, and Tailwind starter kit. Use when Codex must add or change frontend-only behavior such as routes, pages, shared UI, API consumers, auth-gated screens, RBAC UI, query or mutation flows, runtime config, accessibility, e2e smoke coverage, tests, and frontend documentation.
-->

# Frontend Feature Builder

## Overview

Deliver frontend changes that follow the project playbook, preserve route and API contracts, and keep
quality gates green.

## Workflow

1. Read `AGENTS.md`.
1. Read `frontend/docs/frontend_playbook.md`.
1. Read `frontend/docs/foundation_status.md`.
1. Read affected operation docs in `frontend/docs/operations/`.
1. Use `frontend/docs/templates/feature_request.md`, `integration_request.md`, or
   `code_change_request.md` when the request needs clearer acceptance criteria.
1. Confirm route, API, auth, state, UX, a11y, observability, performance, and validation impact.
1. Use `python scripts/scaffold_feature.py frontend <feature-name> --dry-run` to preview new page
   structure when adding a new feature route.
1. Use `python scripts/scaffold_feature.py frontend <feature-name>` only after target paths and
   route scope are clear.
1. Implement within the existing frontend architecture.
1. Add or update tests and docs in the same change.
1. Run relevant frontend validation gates.

## Architecture Rules

- Preserve `app -> features -> shared` dependency direction.
- Compose routes through `frontend/src/app/routes.tsx`.
- Put feature screens under `frontend/src/features/<feature>/`.
- Put reusable cross-feature behavior under `frontend/src/shared/`.
- Use existing API, auth, RBAC, observability, routing, and UI helpers before adding abstractions.
- Keep user-facing text aligned with the existing text catalog pattern.
- Keep loading, empty, error, and unauthorized states explicit.
- Avoid new dependencies unless a current acceptance criterion requires them.

## Documentation Triggers

Update frontend docs when the change affects:

- routes, navigation, route guards, or access policy,
- API consumers, backend OpenAPI sync, or error handling contracts,
- query/mutation retry, invalidation, or cache policy,
- runtime environment variables or fail-fast boot behavior,
- browser security behavior,
- observability events, runtime diagnostics, or support runbook behavior,
- e2e smoke journeys,
- accessibility gate behavior,
- performance budget behavior,
- foundation rules, contracts, or validation gates.

Primary docs:

- `frontend/docs/operations/route_inventory.md`
- `frontend/docs/operations/api_contract_sync.md`
- `frontend/docs/operations/api_consumer_matrix.md`
- `frontend/docs/operations/mutation_policy.md`
- `frontend/docs/operations/runtime_config.md`
- `frontend/docs/operations/browser_security_baseline.md`
- `frontend/docs/operations/observability_events.md`
- `frontend/docs/operations/runtime_error_pipeline.md`
- `frontend/docs/operations/support_diagnostics_runbook.md`
- `frontend/docs/operations/e2e_smoke_suite.md`
- `frontend/docs/operations/accessibility_gate.md`
- `frontend/docs/operations/performance_budget.md`
- `frontend/docs/foundation_status.md`

## Test Expectations

Add focused tests for:

- route rendering and guard behavior,
- page behavior and user interactions,
- API consumer success and error handling,
- query or mutation policy behavior,
- auth/session and RBAC UI behavior,
- accessibility baseline when routes or states change,
- e2e smoke coverage when auth, routing, or error journeys change.

## Validation

Run:

- `npm --prefix frontend run check`
- `npm --prefix frontend run build`

Also run:

- `npm --prefix frontend run test:e2e:ci` when auth, routing, or error journeys change.
- `npm --prefix frontend run openapi:check` when API output should be unchanged.
- `pre-commit run --all-files` when docs, hooks, formatting, Docker, or shared config changed.

## Final Report

Report:

- frontend behavior delivered,
- routes, API consumers, shared modules, and docs changed,
- tests added or updated,
- validation commands run and outcomes,
- commands skipped and why,
- residual risk or follow-up needed.
