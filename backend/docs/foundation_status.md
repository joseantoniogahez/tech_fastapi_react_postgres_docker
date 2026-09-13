# Backend Foundation Status

## Purpose

Capture the current backend foundation state as a single source of truth focused on what exists now.
This document replaces backlog-style historical tracking for backend foundation decisions.

## Current Foundation Snapshot

Status date: `2026-08-12`

- Foundation maturity: `ready for feature delivery`.
- Architecture baseline enforced:
  - Vertical slices (`router -> service -> repository`) per feature.
  - Shared runtime concerns in `app/core`.
  - Router registration centralized in `app/core/setup/routers.py`.
- Runtime and contract baseline active:
  - Canonical endpoint inventory with exhaustive runtime/OpenAPI method, path, status,
    authentication, permission, read-access, and visibility equality.
  - Authorization matrix with scope semantics.
  - Normalized error payload and HTTP mapping.
  - Fail-closed runtime environments and controlled OpenAPI route exposure.
  - Canonical credentialed CORS origins, bounded request correlation, and recursive log redaction.
  - Dependency-free liveness plus typed, bounded, registry-driven readiness for traffic admission.
  - Fixed-window authentication rate limiting with memory for local use and authenticated shared
    Redis required for production-like deployments, including fail-closed outage behavior.
  - UnitOfWork transaction boundary enforcement.
  - Dependency-injection and OpenAPI documentation patterns.

## Active Guardrails

- Canonical engineering rules: `docs/backend_playbook.md`.
- Canonical runtime contracts: `docs/operations/*.md`.
- Architecture annexes: `docs/architecture/*.md`.
- Request workflows for AI execution: `docs/templates/*.md`.
- Preventive endpoint contract: `tests/contracts/test_documentation_contracts.py`.
- Manual PostgreSQL recovery contract: `docs/operations/postgresql_backups.md`; scheduling,
  encryption, storage, and drills remain operator-owned until external automation is selected.

## Required Validation Gates

Run these from repository root before delivery:

- `.\.venv\Scripts\python.exe -m pytest backend\tests` (PowerShell; use
  `./.venv/bin/python` and POSIX paths on POSIX)
- `.\.venv\Scripts\python.exe -m pytest backend\tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`
  (CI-equivalent)
- `.\.venv\Scripts\python.exe -m pytest backend\tests\contracts\test_documentation_contracts.py`
  (endpoint/docs/OpenAPI guard)
- `.\.venv\Scripts\python.exe -m pre_commit run --all-files` (recommended before push)

## Change Management Rules

1. Keep this file current when foundation rules/contracts/gates change.
1. Update affected operation and architecture docs in the same PR as behavior changes.
1. Keep templates aligned with AI request expectations and reviewer needs.
1. Do not add backlog/history tracking documents for foundation unless explicitly requested.
