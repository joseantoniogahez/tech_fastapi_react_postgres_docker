# Frontend E2E Smoke Suite

This document defines the deterministic end-to-end smoke baseline for the frontend foundation.

## Scope

- Critical login journey.
- Protected route navigation behavior.
- Error fallback behavior for protected session validation.
- Admin protected route error diagnostics for RBAC `403 forbidden` responses.
- Admin audit-log route visibility for sessions with `audit_logs:read`.
- Registration, profile update, not-found, permission redirect, and API diagnostic journeys.
- Global logout from the authenticated layout, token removal, login redirect, and protected
  history-return denial.
- Mobile navigation keeps profile and administration at full content width, without horizontal
  overflow at 320 and 390 CSS pixels; following a navigation link closes the menu.

## Runner Contract

- Runner: Playwright (`@playwright/test`).
- Config: `playwright.config.ts`.
- Browser baseline: Chromium only for foundation smoke determinism.
- Test files: `e2e/foundation-smoke.spec.ts`.

## Scenario Inventory

- `keeps profile and administration usable with mobile navigation open`
- `navigates to register and completes the registration flow`
- `completes login flow and lands on welcome page`
- `redirects protected navigation to login when no session token exists`
- `renders protected-route error fallback with request-id diagnostics`
- `loads protected profile route and persists updated account state`
- `logs out from the authenticated layout and denies protected history return`
- `renders admin-users error diagnostics on forbidden RBAC access`
- `loads admin audit log route for audit readers`
- `loads admin assignments workspace and shows direct-read diagnostics`
- `loads admin permissions workspace and shows scope-mutation diagnostics`
- `redirects unauthorized direct admin routes to /welcome`

## Deterministic Setup

- Frontend app server is started by Playwright via `webServer` in `playwright.config.ts`.
- The `test:e2e:ci` lifecycle forces a fresh server even when the shell does not export `CI`.
- API calls are mocked per test with strict route handlers for `**/v1/**`.
- Unhandled API requests fail tests immediately to expose drift or accidental network dependency.
- CI retries are disabled. A scenario that passes only after retry is a failure, not a completed gate.

## Execution Commands

- Local smoke run: `npm --prefix frontend run test:e2e`
- CI-equivalent smoke run: `npm --prefix frontend run test:e2e:ci`
- Browser install (required once per environment): `npm --prefix frontend run e2e:install`

## Failure Artifacts

- Trace on failure: `test-results/**/trace.zip`
- Screenshot on failure: `test-results/**`
- CI output uses line reporter for fast triage.

## Ownership

- Any auth/routing/error behavior changes must update smoke tests when expected behavior changes.
- Any API-path contract change affecting smoke scenarios must update route mocks and this document.
