<!--
name: project-feature-builder
description: Full-stack feature delivery for this FastAPI, React, PostgreSQL, and Docker starter kit. Use when Codex must add or change a user-facing capability that touches both backend and frontend, including API endpoints, data models, auth or RBAC behavior, OpenAPI contract sync, routes, UI state, tests, and project documentation.
-->

# Project Feature Builder

## Overview

Deliver scoped full-stack features in this starter kit while preserving the backend and frontend
contracts. Use canonical repository docs as the source of truth and treat validation gates as the
definition of done.

## Workflow

1. Read `AGENTS.md`.
1. Read `AI_GOVERNED_STARTER_KIT_PLAN.md` when the request affects AI governance, skill behavior,
   starter-kit roadmap, or reusable workflow shape.
1. Read `backend/docs/backend_playbook.md` and `frontend/docs/frontend_playbook.md`.
1. Read both foundation status files:
   - `backend/docs/foundation_status.md`
   - `frontend/docs/foundation_status.md`
1. Read affected backend operation and architecture docs before editing backend behavior.
1. Read affected frontend operation docs before editing frontend behavior.
1. Confirm scope, acceptance criteria, affected contracts, protected files, and validation gates.
1. Use `python scripts/scaffold_feature.py full-stack <feature-name> --dry-run` to preview new
   feature structure when adding a new vertical feature.
1. Use `python scripts/scaffold_feature.py full-stack <feature-name>` only after the target paths and
   scope are clear.
1. Implement the smallest coherent full-stack change.
1. Update tests, OpenAPI artifacts, docs, and inventories in the same change when contracts move.
1. Run matching validation commands and report outcomes.

## Backend Impact Checklist

Consider backend impact when the feature changes:

- API routes, request or response schemas, status codes, or OpenAPI metadata.
- Authentication, current-user behavior, JWT policy, account updates, or bootstrap behavior.
- RBAC permissions, scopes, role assignments, or read-access semantics.
- Persistence models, repositories, Alembic migrations, or transaction boundaries.
- Domain errors, normalized error payloads, logging, observability, outbox, or integration ports.

Relevant docs:

- `backend/docs/operations/api_endpoints.md`
- `backend/docs/operations/authentication.md`
- `backend/docs/operations/authorization_matrix.md`
- `backend/docs/operations/error_mapping.md`
- `backend/docs/architecture/*.md` for DI, UoW, OpenAPI, router registration, or architecture rules.

## Frontend Impact Checklist

Consider frontend impact when the feature changes:

- Routes, navigation, route guards, access policy, or error boundaries.
- API consumers, OpenAPI sync, auth/session behavior, or RBAC UI behavior.
- Query and mutation retry, invalidation, cache behavior, or runtime config.
- User-facing text catalog, loading states, empty states, error recovery, accessibility, or e2e smoke
  journeys.
- Observability events, runtime error diagnostics, browser security, or performance budgets.

Relevant docs:

- `frontend/docs/operations/route_inventory.md`
- `frontend/docs/operations/api_contract_sync.md`
- `frontend/docs/operations/api_consumer_matrix.md`
- `frontend/docs/operations/mutation_policy.md`
- `frontend/docs/operations/runtime_config.md`
- `frontend/docs/operations/e2e_smoke_suite.md`
- `frontend/docs/operations/accessibility_gate.md`
- `frontend/docs/operations/performance_budget.md`

## Implementation Rules

- Preserve backend vertical slices and frontend `app -> features -> shared` dependency direction.
- Prefer existing project helpers, contracts, services, test utilities, and style conventions.
- Keep API routes under `/v1` unless the request explicitly changes API versioning.
- Update backend docs and frontend docs when behavior or contracts change.
- Run `npm --prefix frontend run openapi:sync` when backend OpenAPI output changes.
- Do not add dependencies unless a current acceptance criterion requires them.

## Validation

Run the smallest complete gate set for the change.

Backend:

- `python -m pytest backend/tests`
- `python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`

Frontend:

- `npm --prefix frontend run check`
- `npm --prefix frontend run test:e2e:ci` when auth, routing, or error journeys change.
- `npm --prefix frontend run build`

Repository:

- `pre-commit run --all-files` when docs, hooks, formatting, Docker, or shared config changed.

## Final Report

Report:

- feature behavior delivered,
- backend and frontend files changed,
- docs and contracts updated,
- validation commands run and outcomes,
- commands skipped and why,
- residual risk or follow-up needed.
