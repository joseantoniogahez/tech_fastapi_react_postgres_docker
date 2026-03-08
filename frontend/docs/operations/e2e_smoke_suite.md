# Frontend E2E Smoke Suite

This document defines the deterministic end-to-end smoke baseline for the frontend foundation.

## Scope

- Critical login journey.
- Protected route navigation behavior.
- Error fallback behavior for protected session validation.

## Runner Contract

- Runner: Playwright (`@playwright/test`).
- Config: `playwright.config.ts`.
- Browser baseline: Chromium only for foundation smoke determinism.
- Test files: `e2e/foundation-smoke.spec.ts`.

## Deterministic Setup

- Frontend app server is started by Playwright via `webServer` in `playwright.config.ts`.
- API calls are mocked per test with strict route handlers for `**/v1/**`.
- Unhandled API requests fail tests immediately to expose drift or accidental network dependency.

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
