<!--
name: project-reviewer
description: Review changes against this AI-governed FastAPI, React, PostgreSQL, and Docker starter kit. Use when Codex is asked to review a diff, branch, pull request, implementation, architecture change, documentation change, or readiness state, especially for bugs, regressions, missing tests, docs drift, contract drift, auth or RBAC risk, security issues, and validation gaps.
-->

# Project Reviewer

## Overview

Review changes for correctness and project fit. Lead with risks and concrete findings, not a broad
summary.

## Workflow

1. Read `AGENTS.md`.
1. Identify changed files and classify the change as backend, frontend, full-stack, integration,
   documentation, AI governance, or bootstrap work.
1. Read the affected playbooks, foundation status files, operation docs, architecture docs, and
   templates for that classification.
1. Inspect the diff and nearby code.
1. Check behavior against documented contracts and validation expectations.
1. Report findings first, ordered by severity, with file and line references.

## Review Priorities

Prioritize:

- behavioral regressions,
- missing or weak tests,
- API, OpenAPI, route, auth, RBAC, or error-contract drift,
- docs and inventory drift,
- migration, transaction, persistence, or data integrity bugs,
- frontend route guard, cache, mutation, accessibility, or e2e smoke gaps,
- security, secret handling, dependency, and runtime config risks,
- observability or diagnostics regressions,
- validation commands that should have run but did not.

## Backend Review Checklist

When backend files change, verify:

- feature boundaries remain vertical where appropriate,
- router, service, repository, schemas, models, and dependencies follow local patterns,
- authorization policy and permission docs stay synchronized,
- endpoint inventory documents route, auth, permission, status, and error behavior,
- domain errors map to the normalized payload contract,
- UoW and transaction behavior remain correct,
- migrations match model changes and are safe,
- tests cover router, service, repository, permission, and docs contracts as applicable.

## Frontend Review Checklist

When frontend files change, verify:

- dependency direction remains `app -> features -> shared`,
- routes and route inventory stay synchronized,
- API consumers and OpenAPI artifacts stay synchronized,
- query and mutation policies follow documented retry and invalidation rules,
- auth/session/RBAC UI behavior is explicit and test-covered,
- loading, empty, error, and unauthorized states are handled,
- accessibility and e2e smoke coverage are updated when affected,
- performance budget, runtime config, observability, and diagnostics contracts remain intact.

## Documentation and Governance Review Checklist

When docs, templates, skills, or AI governance files change, verify:

- canonical docs remain the source of truth,
- docs do not duplicate playbooks unnecessarily,
- task routing and validation expectations remain clear,
- foundation status changes only when foundation rules, contracts, or gates change,
- skills contain concise workflow instructions and point to project docs,
- skill frontmatter includes only `name` and `description`,
- validation commands are documented and realistic.

## Output Format

Use this order:

1. Findings, ordered by severity.
1. Open questions or assumptions.
1. Concise summary.
1. Validation gaps or residual risk.

For each finding, include:

- severity,
- file and line reference,
- concrete problem,
- likely impact,
- suggested fix.

If no issues are found, say that clearly and still mention remaining test or validation risk.
