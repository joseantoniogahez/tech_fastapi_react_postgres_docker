# Frontend Dependency and Supply-Chain Policy

This document defines dependency-risk thresholds and enforcement rules for frontend package changes.

## Risk Threshold Policy

- Audit scope: production dependencies only (`--omit=dev`).
- Maximum allowed vulnerabilities:
  - `critical`: `0`
  - `high`: `0`
- Policy source file: `frontend/security/dependency_audit_policy.json`.

## Enforcement

- Validation command:
  - `npm --prefix frontend run deps:audit`
- Standard quality gate:
  - `npm --prefix frontend run check` includes dependency audit gate.
- Operational failures fail closed: process errors, signals, unexpected exit statuses, npm error
  reports, malformed JSON, missing vulnerability metadata, and invalid vulnerability counts reject
  the gate.
- Exit status `1` is accepted for evaluation only when npm returned a structurally valid audit
  report; the configured `high` and `critical` thresholds then determine whether the gate passes.
- If audit fails:
  1. Upgrade/replace vulnerable dependency.
  1. Re-run audit and confirm threshold compliance.
  1. Document risk treatment in PR notes if exceptional handling is needed.

## Reviewer Requirements

- Package and lockfile changes must include dependency audit results.
- Any policy-threshold change requires explicit reviewer approval and rationale.
