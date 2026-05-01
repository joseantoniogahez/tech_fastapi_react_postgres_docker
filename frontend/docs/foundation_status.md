# Frontend Foundation Status

## Purpose

Capture the current frontend foundation state as a single source of truth focused on what exists now.
This document replaces backlog-style historical tracking for frontend foundation decisions.

## Current Foundation Snapshot

Status date: `2026-05-01`

- Foundation maturity: `ready for feature delivery`.
- Architecture baseline enforced:
  - `app -> features -> shared` dependency direction.
  - Centralized route composition in `src/app/routes.tsx`.
- Runtime and quality contracts active:
  - API contract sync and drift prevention.
  - API consumer/error matrix.
  - Mutation/query policy contracts.
  - Runtime config validation and fail-fast boot.
  - Browser security baseline.
  - Observability and runtime error pipeline.
  - Accessibility baseline gate.
  - Performance budget gate.
  - E2E smoke baseline for auth/routing/error journeys.

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
