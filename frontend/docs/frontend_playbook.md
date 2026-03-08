# Frontend Engineering Playbook

This playbook is the decision source for frontend implementation and review.
If another frontend document conflicts with this file, update the conflicting document.

## Goal

Provide a stable frontend foundation for iterative feature delivery with predictable architecture, testing, and review criteria.

## Architecture Map

Current frontend structure:

- `src/main.tsx`: app bootstrap and top-level providers.
- `src/app`: application composition (`routes.tsx`, `query-client.ts`, global styles).
- `src/features/<feature>`: feature-level pages and feature-specific UI behavior.
- `src/shared`: cross-feature modules (`api`, `auth`, `routing`, `i18n`, `ui`).
- `src/test`: test setup and shared testing runtime hooks.

Dependency direction:

- `app` composes `features` and `shared`.
- `features` can depend on `shared`.
- `shared` must not depend on `features`.

## Non-Negotiable Rules

1. Route definitions are centralized in `src/app/routes.tsx`.
1. Shared API calls must flow through `src/shared/api/http.ts`.
1. API error normalization must be handled in `src/shared/api/errors.ts`.
1. Session/auth state operations must be handled through `src/shared/auth/session.ts`.
1. Token persistence behavior must be encapsulated in `src/shared/auth/storage.ts`.
1. Protected route behavior must stay in `src/shared/routing/ProtectedRoute.tsx`.
1. User-facing text must be sourced from `src/shared/i18n/ui-text.ts`; UI tests must assert labels/titles using `t(...)` (not hardcoded catalog literals).
1. Query behavior must be configured via `src/app/query-client.ts` and explicit query options.
1. Every behavior change in auth/session/routing/api error handling requires tests.
1. Frontend docs and foundation status must be updated in the same PR when process/rules change.
1. Frontend docs must remain compliant with documentation contract tests in `src/contracts/docs.contract.test.ts`.
1. Direct feature-page imports are owned by `src/app/routes.tsx`; app modules outside route composition must not import `src/features/*`.
1. Cross-feature runtime imports are disallowed; feature modules can only depend on `src/shared`.
1. Route inventory must be updated in `docs/operations/route_inventory.md` when route behavior changes.
1. Backend API contract sync artifact must stay current in `contracts/openapi/backend_openapi.json`.
1. Runtime environment config must be validated via `src/shared/api/env.ts` and stay aligned with `docs/operations/runtime_config.md`.
1. API/routing/runtime diagnostics must emit structured events via `src/shared/observability/events.ts`.
1. Global runtime error handlers must stay installed via `src/shared/observability/runtime-errors.ts`.
1. Core auth/routing/error journeys must remain covered by `e2e/foundation-smoke.spec.ts`.
1. Baseline accessibility checks in `src/app/accessibility.routes.test.tsx` must stay green for UI changes.
1. Bundle budget policy in `performance/bundle_budget.json` must be respected by `npm --prefix frontend run build`.

## Query Policy Matrix

| Domain        | Retry Policy                                     | Stale Time  | Refetch On Window Focus |
| ------------- | ------------------------------------------------ | ----------- | ----------------------- |
| Default query | Retry only transient/network errors, max 1 retry | `30_000 ms` | `false`                 |
| Session query | No retry                                         | `60_000 ms` | `true`                  |

Reference implementation: `src/app/query-policy.ts`.

## Mutation Policy Matrix

| Domain               | Retry Policy                                     | Invalidation Strategy                                          |
| -------------------- | ------------------------------------------------ | -------------------------------------------------------------- |
| Default mutation     | Retry only transient/network errors, max 1 retry | Domain-driven; explicit in caller                              |
| Auth login mutation  | No retry                                         | Write-through `SESSION_QUERY_KEY` and invalidate session query |
| Auth logout mutation | No retry                                         | Clear `SESSION_QUERY_KEY` and invalidate session query         |

Reference implementation: `src/app/mutation-policy.ts`.

## Request and Template Conventions

Use these templates in `docs/templates/`:

- `feature_request.md`
- `integration_request.md`
- `code_change_request.md`

Required request quality:

1. State the problem and measurable goal.
1. Separate in-scope from out-of-scope behavior.
1. Define API/auth/routing/state implications.
1. Define acceptance criteria and required validation commands.
1. Include reviewer-focused checks.

## AI Operating Protocol

Before coding:

1. Read this playbook and `docs/foundation_status.md`.
1. Confirm affected foundation guardrails and required validation gates in `docs/foundation_status.md`.
1. Confirm affected runtime contracts (routing/auth/api/i18n/testing).

During coding:

1. Keep module boundaries and dependency direction intact.
1. Add/update tests with each behavior change.
1. Keep docs and foundation status synchronized with implementation state.

Before delivery:

1. Run `npm --prefix frontend run check`.
1. Run `npm --prefix frontend run build` when routing/build-sensitive changes are included.
1. Run `.\.venv\Scripts\pre-commit.exe run --all-files`.

## Reviewer Checklist

- [ ] Changes respect frontend module boundaries and dependency direction.
- [ ] Routing/auth/api error behavior remains explicit and test-covered.
- [ ] Route inventory and access policy contracts remain synchronized with router configuration.
- [ ] API consumer matrix and error contract docs remain synchronized with shared API consumers.
- [ ] Browser security baseline contract is preserved or intentionally updated with review notes.
- [ ] Dependency policy gate is satisfied for package/lockfile changes.
- [ ] Observability events remain structured, redaction-safe, and correlation-ready.
- [ ] Support diagnostics runbook is updated when observability/error behavior changes.
- [ ] E2E smoke suite remains aligned with auth/routing/error contracts and passes in CI-equivalent mode.
- [ ] Accessibility baseline gate remains green for affected routes/states.
- [ ] Bundle/performance budget impact is assessed for dependency or route-level changes.
- [ ] Query policy decisions are intentional and documented when changed.
- [ ] User-facing text remains catalog-based and encoding-safe.
- [ ] Foundation status is updated when rules/contracts/gates change.
- [ ] Validation commands pass.
