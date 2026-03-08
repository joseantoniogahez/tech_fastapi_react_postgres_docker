# Frontend API Contract Sync

This document defines how frontend API contract artifacts stay synchronized with backend OpenAPI output.

## Contract Artifact

- Source of truth runtime schema: backend FastAPI OpenAPI output (`app.openapi()`).
- Frontend artifact path: `frontend/contracts/openapi/backend_openapi.json`.
- Artifact format: stable, sorted JSON (deterministic for review diffs).

## Commands

- Sync artifact:
  - `npm --prefix frontend run openapi:sync`
- Validate artifact freshness:
  - `npm --prefix frontend run openapi:check`

## CI/Local Drift Gate

- `npm --prefix frontend run check` must include `openapi:check`.
- If backend contracts change and artifact is stale, check must fail.
- Required remediation:
  1. Run `openapi:sync`.
  1. Review generated diff.
  1. Update frontend consumers/docs/tests if contract behavior changed.

## Reviewer Checklist

- [ ] OpenAPI artifact was refreshed when backend endpoint contracts changed.
- [ ] Generated artifact diff is intentional and explained in PR notes.
- [ ] Frontend consumer and error contract docs remain synchronized after update.
