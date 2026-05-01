# Backend Foundation Status

## Purpose

Capture the current backend foundation state as a single source of truth focused on what exists now.
This document replaces backlog-style historical tracking for backend foundation decisions.

## Current Foundation Snapshot

Status date: `2026-05-01`

- Foundation maturity: `ready for feature delivery`.
- Architecture baseline enforced:
  - Vertical slices (`router -> service -> repository`) per feature.
  - Shared runtime concerns in `app/core`.
  - Router registration centralized in `app/core/setup/routers.py`.
- Runtime and contract baseline active:
  - Canonical endpoint inventory and auth requirements.
  - Authorization matrix with scope semantics.
  - Normalized error payload and HTTP mapping.
  - UnitOfWork transaction boundary enforcement.
  - Dependency-injection and OpenAPI documentation patterns.

## Active Guardrails

- Canonical engineering rules: `docs/backend_playbook.md`.
- Canonical runtime contracts: `docs/operations/*.md`.
- Architecture annexes: `docs/architecture/*.md`.
- Request workflows for AI execution: `docs/templates/*.md`.

## Required Validation Gates

Run these from repository root before delivery:

- `python -m pytest backend/tests`
- `python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100` (CI-equivalent)
- `pre-commit run --all-files` (recommended before push)

## Change Management Rules

1. Keep this file current when foundation rules/contracts/gates change.
1. Update affected operation and architecture docs in the same PR as behavior changes.
1. Keep templates aligned with AI request expectations and reviewer needs.
1. Do not add backlog/history tracking documents for foundation unless explicitly requested.
