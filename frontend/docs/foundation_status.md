# Frontend Foundation Status

## Purpose

Capture the current frontend foundation state as a single source of truth focused on what exists now.
This document replaces backlog-style historical tracking for frontend foundation decisions.

## Current Foundation Snapshot

Status date: `2026-08-28`

- Foundation maturity: `ready for feature delivery`.
- Architecture baseline enforced:
  - `app -> features -> shared` dependency direction.
  - Centralized route composition in `src/app/routes.tsx`.
- Runtime and quality contracts active:
  - API contract sync and drift prevention.
  - API consumer/error matrix.
  - Cross-stack `rate_limited` and `service_unavailable` authentication taxonomy with request-ID
    diagnostics and no implicit retry semantics.
  - Query transient retry plus a no-inherited-retry mutation default; idempotent mutation opt-ins
    require an explicit proven backend contract.
  - Mandatory runtime parsing for JSON API responses and a separate strict `204` no-content path,
    with correlated `invalid_response` diagnostics for contract mismatches.
  - Runtime config validation and fail-fast boot.
  - Browser security baseline enforced by generated production response headers and HTTP smoke.
  - Privacy-safe API diagnostics, recursively redacted observability, and bounded cause-based
    runtime error correlation.
  - Accessibility baseline gate with axe/jsdom route coverage, token-level text/control contrast
    thresholds, deterministic field focus outlines, and retained manual browser review.
  - Vitest unit/coverage execution capped at four workers so jsdom integration cases retain the
    five-second per-test contract without host-core-count saturation.
  - Performance budget gate.
  - E2E smoke baseline for auth/routing/error journeys with exact equality between the documented
    and implemented scenario inventories.
  - Mobile open-navigation reflow is covered at 320 and 390 CSS pixels for profile, users, and
    roles, with full-width content and automatic menu closure after navigation.

## Active Guardrails

- Canonical engineering rules: `docs/frontend_playbook.md`.
- Canonical runtime contracts: `docs/operations/*.md`.
- Request workflows for AI execution: `docs/templates/*.md`.
- Documentation contracts: `src/contracts/docs.contract.test.ts`.

## Required Validation Gates

Run these from `frontend/` before delivery:

- `npm run check`
- `npm run test:e2e:ci` (required when auth/routing/error journeys are affected)
- `npm run build`

## Change Management Rules

1. Keep this file current when foundation rules/contracts/gates change.
1. Update affected operation docs in the same PR as behavior changes.
1. Keep templates aligned with AI request expectations and reviewer needs.
1. Do not add backlog/history tracking documents for foundation unless explicitly requested.
