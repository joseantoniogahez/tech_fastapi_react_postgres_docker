# Backend Engineering Playbook

This playbook is the decision source for backend implementation and review.
If any other backend document conflicts with this file, update the conflicting document.

## Architecture Map

Current top-level backend structure:

- `app/main.py`: runtime entrypoint.
- `app/core`: cross-feature runtime modules (setup, config, db, security, authorization, errors, common helpers).
- `app/features/<feature>`: vertical slices (router, service, repository, schemas, models, feature OpenAPI docs).
- `app/integrations`: external system ports.
- `utils`: operational scripts and local tooling helpers.

Dependency direction:

- `router -> service -> repository -> core db/runtime`.
- features may import `app.core.*`.
- cross-feature imports are restricted and validated by architecture tests.

## Router Inventory

Router registration is centralized in `app/core/setup/routers.py`.

### Registered Router Modules

- `app.features.health.router`
- `app.features.auth.router`
- `app.features.rbac.router`

All registered routers are mounted under API prefix `/v1`.

## Non-Negotiable Engineering Rules

1. Keep vertical ownership inside the feature slice.
1. Keep HTTP concerns in routers only.
1. Keep business orchestration in services only.
1. Keep persistence logic in repositories only.
1. Do not instantiate services directly in routers; consume typed dependencies from `app/core/setup/dependencies.py`.
1. Write operations must run inside `UnitOfWork` (`app/core/db/uow.py`) via `async with self.unit_of_work`.
1. Repository write methods must not call `commit`; commit/rollback is controlled by UoW.
1. New protected endpoints must use explicit authorization dependencies and documented permission scopes.
1. New permissions must be added to `app/core/authorization/catalog.py` and documented in `docs/operations/authorization_matrix.md`.
1. OpenAPI metadata must stay in feature OpenAPI modules, not inline in routers.
1. Public endpoint contracts must be reflected in `docs/operations/api_endpoints.md`.
1. Domain errors must map to the normalized payload contract in `docs/operations/error_mapping.md`.
1. Naming guardrails must stay compliant with tests (for example, avoid generic `id` parameter names in routers/services).
1. Foundation status must stay current in `docs/foundation_status.md` when baseline rules/contracts/gates change.

## Add a New Feature Workflow

1. Create `app/features/<feature>/` with `router.py`, `service.py`, `repository.py`, `schemas/api.py`, and `schemas/app.py`.
1. Add `models.py` only when the feature owns persistence tables.
1. Register the router module in `ROUTER_MODULES` inside `app/core/setup/routers.py`.
1. Add or update dependency providers in `app/core/setup/dependencies.py`.
1. Add or update authz dependencies for protected endpoints.
1. Add/update OpenAPI metadata constants in feature OpenAPI modules and consume them in routers.
1. Add tests for service behavior, repository behavior, router behavior, and architecture boundary expectations.
1. Update operation contracts:

- `docs/operations/api_endpoints.md`
- `docs/operations/authorization_matrix.md` (if permission-protected)
- `docs/operations/authentication.md` (if auth behavior changes)
- `docs/operations/error_mapping.md` (if error contract changes)

## Add a New Integration Workflow

1. Define or extend integration ports under `app/integrations`.
1. Use feature services to orchestrate integration calls.
1. Keep integration payload contracts in application schemas (`app/core/common/integration.py` or feature-local app schemas).
1. Wrap persistence side effects in UoW where atomic writes are required.
1. Add observability events using `app/core/common/observability.py`.
1. Add tests for integration-facing service behavior and failure scenarios.
1. Update relevant operations docs and architecture annex docs when integration behavior changes public contracts or engineering rules.

## AI Operating Protocol

Before coding:

1. Read this playbook.
1. Read all impacted operation contracts.
1. Read the relevant architecture annex for the targeted subsystem.
1. Validate whether requested changes imply new permissions, endpoint docs, or error contract updates.

During coding:

1. Keep boundaries and dependency direction intact.
1. Update docs in the same change when behavior contracts change.
1. Keep tests and docs synchronized; do not leave operation contracts stale.

Before delivering:

1. Run backend tests (at minimum impacted suites plus contract tests).
1. Confirm router inventory and docs references remain valid.
1. Confirm new endpoints, permissions, and auth rules are documented.

## Reviewer Approval Checklist

- [ ] Feature boundaries remain vertical (`router/service/repository/schemas`).
- [ ] DI/UoW patterns are preserved.
- [ ] Authorization dependencies are explicit and scope-correct.
- [ ] Operation docs are updated for every public contract change.
- [ ] Error payload/mapping contract remains normalized.
- [ ] New or changed integrations include failure handling and observability.
- [ ] Contract tests and affected backend tests pass.
