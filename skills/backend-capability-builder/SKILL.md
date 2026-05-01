<!--
name: backend-capability-builder
description: Backend feature and capability delivery for this FastAPI starter kit. Use when Codex must add or change backend-only behavior such as API endpoints, vertical feature slices, services, repositories, schemas, SQLAlchemy models, Alembic migrations, auth, RBAC permissions, outbox behavior, integration ports, tests, and backend documentation.
-->

# Backend Capability Builder

## Overview

Deliver backend changes that follow the project playbook, preserve runtime contracts, and keep tests
and docs synchronized with behavior.

## Workflow

1. Read `AGENTS.md`.
1. Read `backend/docs/backend_playbook.md`.
1. Read `backend/docs/foundation_status.md`.
1. Read affected operation docs in `backend/docs/operations/`.
1. Read affected architecture annexes in `backend/docs/architecture/`.
1. Use `backend/docs/templates/feature_request.md`, `integration_request.md`, or
   `code_change_request.md` when the request needs clearer acceptance criteria.
1. Confirm API, data, auth, RBAC, error, observability, and validation impact.
1. Use `python scripts/scaffold_feature.py backend <feature-name> --dry-run` to preview new backend
   feature structure when adding a new vertical feature.
1. Use `python scripts/scaffold_feature.py backend <feature-name>` only after target paths and scope
   are clear.
1. Implement within the existing backend architecture.
1. Add or update tests and docs in the same change.
1. Run relevant backend validation gates.

## Architecture Rules

- Keep feature behavior in vertical slices under `backend/app/features/<feature>/`.
- Use the local `router -> service -> repository` shape where persistence is involved.
- Keep shared runtime concerns in `backend/app/core/`.
- Register routers through the documented router registration pattern.
- Use existing dependency-injection and UnitOfWork patterns.
- Keep request/response API schemas separate from application schemas when the feature uses that
  split.
- Keep domain errors mapped to the normalized error payload contract.
- Use integration ports in `backend/app/integrations/` before binding to a concrete provider.

## Documentation Triggers

Update backend docs when the change affects:

- endpoint inventory, auth requirements, permissions, status codes, or response shape,
- authentication flow, bootstrap behavior, account update policy, or JWT policy,
- permission catalog, scope semantics, role assignments, or read-access classification,
- domain error mapping or normalized error payload behavior,
- DI, UoW, OpenAPI metadata, router registration, or architecture rules,
- foundation rules, contracts, or validation gates.

Primary docs:

- `backend/docs/operations/api_endpoints.md`
- `backend/docs/operations/authentication.md`
- `backend/docs/operations/authorization_matrix.md`
- `backend/docs/operations/error_mapping.md`
- `backend/docs/architecture/*.md`
- `backend/docs/foundation_status.md`

## Test Expectations

Add focused tests for:

- router behavior and HTTP contract,
- service behavior and domain errors,
- repository behavior when persistence changes,
- permission coverage when RBAC changes,
- documentation contract coverage when docs or public contracts change,
- migrations when models or constraints change.

## Validation

Run:

- `python -m pytest backend/tests`
- `python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`

Also run:

- `pre-commit run --all-files` when docs, hooks, formatting, Docker, or shared config changed.

## Final Report

Report:

- backend behavior delivered,
- routes, permissions, models, migrations, and docs changed,
- tests added or updated,
- validation commands run and outcomes,
- commands skipped and why,
- residual risk or follow-up needed.
