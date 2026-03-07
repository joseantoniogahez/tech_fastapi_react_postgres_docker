# Feature Growth Backlog

## Goal

Keep this backend as a neutral feature-based template that can grow by vertical slices without reintroducing layered coupling.

## Near-Term Items

- Add one additional feature module beyond `auth`, `health`, `rbac`, and `outbox` to reinforce the vertical-slice baseline.
- Add one concrete adapter implementation for a port in `app/integrations` (message broker, jobs, files, or search).
- Add architecture tests that prevent forbidden imports from `app/core/setup` into feature repositories.
- Add a smoke test for `alembic upgrade head` against a clean SQLite database.
- Add contract checks that architecture annex docs stay aligned with current module inventory.

## Guardrails

- Shared code belongs in `app/core` only when it is truly cross-feature.
- Feature logic should stay inside `app/features/<feature>`.
- New public permissions must be added to `app/core/authorization/catalog.py` and documented in `docs/operations/authorization_matrix.md`.
- Public endpoints must be reflected in `docs/operations/api_endpoints.md`.
