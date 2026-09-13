# AI Agent Operating Guide

This repository is a FastAPI, React, PostgreSQL, and Docker starter kit intended to become an
AI-governed foundation for new applications.

Use this file as the first orientation point for AI-assisted work. It routes tasks to the canonical
project docs, validation gates, and delivery expectations without replacing the backend or frontend
playbooks.

## Mission

Build and evolve applications from this foundation with AI assistance while preserving:

- documented architecture boundaries,
- explicit API, auth, RBAC, routing, and runtime contracts,
- test and documentation gates,
- small, reviewable, production-minded changes.

## First Reading Rule

Always start here, then read only the canonical docs needed for the task.

For AI-governance work, also read:

- `docs/ai/README.md`

For repository setup and service overview, read:

- `README.md`
- `backend/README.md` when backend behavior is involved.
- `frontend/README.md` when frontend behavior is involved.

## Task Routing

Backend-only feature or capability:

- Read `backend/docs/backend_playbook.md`.
- Read `backend/docs/foundation_status.md`.
- Read affected backend operation docs in `backend/docs/operations/`.
- Read affected architecture annexes in `backend/docs/architecture/`.
- Use `backend/docs/templates/feature_request.md`, `integration_request.md`, or
  `code_change_request.md` as the request shape when scope is not already explicit.

Frontend-only feature or capability:

- Read `frontend/docs/frontend_playbook.md`.
- Read `frontend/docs/foundation_status.md`.
- Read affected frontend operation docs in `frontend/docs/operations/`.
- Use `frontend/docs/templates/feature_request.md`, `integration_request.md`, or
  `code_change_request.md` as the request shape when scope is not already explicit.

Full-stack feature:

- Read the backend and frontend playbooks.
- Read both foundation status files.
- Use `docs/ai/templates/full_stack_feature_request.md` when scope is not already explicit.
- Read backend docs for API, auth, RBAC, data, errors, UoW, router registration, and OpenAPI when
  affected.
- Read frontend docs for routes, API sync, API consumers, query/mutation policy, runtime config,
  auth/session, a11y, performance, and e2e smoke coverage when affected.
- Treat backend OpenAPI output and frontend API contract sync as one delivery surface.

Integration work:

- Read the backend playbook integration workflow.
- Read affected backend architecture docs and operation docs.
- Read frontend API consumer and runtime/error docs if the integration changes UI behavior.
- Prefer existing ports/adapters before adding concrete providers.

Review work:

- Use a code-review stance.
- Read this file plus affected backend/frontend playbooks and operation docs.
- Lead with findings ordered by severity.
- Prioritize behavioral regressions, missing tests, contract drift, docs drift, auth/RBAC mistakes,
  security risks, and validation gaps.

New application bootstrap:

- Read `docs/ai/start_new_project.md`.
- Read `docs/ai/new_app_bootstrap_checklist.md`.
- Read `docs/ai/template_reuse_contract.md`.
- Read root and service READMEs.
- Use `docs/ai/templates/new_app_request.md` when app identity, scope, or bootstrap mode is not
  already explicit.
- Use the root `.venv` to run `scripts/bootstrap_new_app.py` with required `--source-repository` and
  `--source-revision`; preview before applying an in-place bootstrap.
- Bootstrap only a clean compatible snapshot once, retain generated provenance, and use a separate
  reviewed procedure for later identity changes.
- Identify app name, domain, roles, initial routes, initial data model, integrations, deployment
  target, and branding terms before making broad renames.
- Update project identity consistently across Compose names, env examples, JWT issuer/audience,
  package metadata, README text, and visible frontend naming.

Documentation-only work:

- Read the docs index for the affected side:
  - `backend/docs/README.md`
  - `frontend/docs/README.md`
- Keep docs aligned with contract tests.
- Update foundation status only when foundation rules, contracts, or validation gates change.

Application backlog work:

- Do not create a default or example application backlog in this starter kit.
- Use `docs/ai/backlog_tracking.md` only after a derived application explicitly declares its
  canonical backlog, plan directories, ownership, status, and evidence policy.
- Before activating an item, create its durable plan from
  `docs/ai/templates/backlog_item_plan.md`; update the exact resumption point before every pause.

## Non-Negotiable Rules

1. Keep canonical docs as the source of truth.
1. Do not duplicate backend/frontend playbooks inside skills or new AI docs.
1. Follow existing architecture patterns before introducing new abstractions.
1. Do not add dependencies speculatively.
1. Update docs in the same change when behavior, contracts, routes, permissions, runtime rules, or
   validation gates change.
1. Keep backend features in vertical slices unless an existing core/shared module owns the concern.
1. Keep frontend dependency direction aligned with `app -> features -> shared`.
1. Keep API routes under the backend `/v1` contract unless explicitly changing the API versioning
   strategy.
1. Keep auth, authorization, and error behavior explicit and test-covered.
1. Preserve unrelated user changes; do not revert files outside the requested work.

## Governed Python Commands

After the repository-root `.venv` exists, every local developer or agent Python command runs from
the repository root with `.\.venv\Scripts\python.exe` on PowerShell or `./.venv/bin/python` on
POSIX. Invoke Python tools as modules, for example `-m pytest`, `-m pre_commit`, `-m mypy`, and
`-m pip_audit`. Global Python is allowed only to create `.venv`; CI jobs and containers may use
their explicitly provisioned isolated interpreter. Scripts must not silently fall back to a global
interpreter.

## Documentation Update Rules

Backend docs to consider:

- `backend/docs/operations/api_endpoints.md` for endpoint, status, auth, and permission changes.
- `backend/docs/operations/authentication.md` for auth/session/account behavior changes.
- `backend/docs/operations/authorization_matrix.md` for permission, scope, and RBAC policy changes.
- `backend/docs/operations/error_mapping.md` for domain error or HTTP mapping changes.
- `backend/docs/architecture/*.md` for DI, UoW, router registration, OpenAPI, or architecture rule
  changes.
- `backend/docs/foundation_status.md` only when backend foundation rules, contracts, or gates change.

Frontend docs to consider:

- `frontend/docs/operations/route_inventory.md` for route or access-policy changes.
- `frontend/docs/operations/api_contract_sync.md` for OpenAPI sync behavior changes.
- `frontend/docs/operations/api_consumer_matrix.md` for frontend API consumer changes.
- `frontend/docs/operations/mutation_policy.md` for query/mutation retry or invalidation changes.
- `frontend/docs/operations/runtime_config.md` for environment variable or boot validation changes.
- `frontend/docs/operations/browser_security_baseline.md` for browser security policy changes.
- `frontend/docs/operations/observability_events.md` and
  `frontend/docs/operations/runtime_error_pipeline.md` for diagnostics changes.
- `frontend/docs/operations/e2e_smoke_suite.md` for auth/routing/error smoke coverage changes.
- `frontend/docs/operations/accessibility_gate.md` for accessibility rule or coverage changes.
- `frontend/docs/operations/performance_budget.md` for bundle budget changes.
- `frontend/docs/foundation_status.md` only when frontend foundation rules, contracts, or gates
  change.

AI governance docs to consider:

- `AGENTS.md` when task routing, required reading, non-negotiable rules, or validation expectations
  change.
- `docs/ai/README.md` when repository-level AI workflow docs are added, removed, or reorganized.
- `docs/ai/start_new_project.md` when the new-project bootstrap workflow changes.
- `docs/ai/templates/*.md` when full-stack or new-app request shape changes.
- `docs/ai/new_app_bootstrap_checklist.md` when new-app identity or validation workflow changes.
- `docs/ai/backlog_tracking.md` and `docs/ai/templates/backlog_item_plan.md` when a derived
  application's backlog activation, status, evidence, archive, or handoff contract changes.

## Validation Matrix

Backend-only change:

- `.\.venv\Scripts\python.exe -m pytest backend\tests` (PowerShell) or
  `./.venv/bin/python -m pytest backend/tests` (POSIX).
- Add `--cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100` for the coverage gate.
- Run `-m pre_commit run --all-files` through the same interpreter when docs, hooks, formatting,
  Docker, or shared config changed.

Frontend-only change:

- `npm --prefix frontend run check`
- `npm --prefix frontend run test:e2e:ci` when auth, routing, or error journeys change.
- `npm --prefix frontend run build`

Full-stack change:

- Run backend validation.
- Run `npm --prefix frontend run openapi:sync` when API output changed.
- Run `npm --prefix frontend run openapi:check` when API output should be unchanged.
- Run frontend validation.
- Run `-m pre_commit run --all-files` through the root `.venv` before push-level confidence when
  practical.

Documentation-only change:

- Run relevant documentation contract tests when available.
- Run `-m pre_commit run --files <changed-docs>` through the root `.venv` or targeted Markdown
  hooks when practical.

New app bootstrap:

- Validate all five canonical Docker Compose render forms with `.env_examples`.
- Run backend tests.
- Run frontend check, smoke e2e, and build.

## Delivery Workflow

1. Classify the task using the routing section.
1. Read the required docs before coding.
1. Identify acceptance criteria, affected contracts, allowed files, protected files, and validation
   gates.
1. Use `scripts/scaffold_feature.py` when creating a new backend, frontend, or full-stack feature
   structure.
1. Make the smallest coherent change that satisfies the request.
1. Add or update tests with the same change.
1. Update affected docs and contract inventories.
1. Run the validation commands that match the task.
1. Report changed files, validation results, skipped validations, and residual risk.

## When to Ask Before Acting

Ask a concise question only when:

- the requested behavior is ambiguous enough that implementation would likely be wrong,
- a broad rename or new app bootstrap lacks required identity/domain details,
- a dependency or infrastructure provider choice is required,
- the change could remove existing behavior or data,
- the task conflicts with documented contracts.

Otherwise, make a reasonable assumption, implement, validate, and report it.

## Final Response Expectations

For implementation work, include:

- what changed,
- key files touched,
- validation commands run and results,
- commands not run and why,
- any follow-up that directly continues the requested work.

For reviews, include:

- findings first, ordered by severity, with file and line references,
- open questions or assumptions,
- concise summary only after findings.

## Project Skills

Repository-local skills live under `skills/`. When available in the active Codex environment, use
them as task-specific operating modes while keeping this file as the root orientation guide. When
they are not auto-discovered, invoke them by path or install/copy them into the active Codex skills
location.

Use `skills/README.md` as the project skill catalog and manual activation guide.
Use `.\.venv\Scripts\python.exe scripts\install_project_skills.py` on PowerShell or
`./.venv/bin/python scripts/install_project_skills.py` on POSIX to preview or install project
skills. The installer validates the complete local pack before discovery and commits a requested
write batch transactionally.

Project skill pack:

- `skills/project-feature-builder`
- `skills/backend-capability-builder`
- `skills/frontend-feature-builder`
- `skills/project-reviewer`
- `skills/new-app-bootstrapper`
- `skills/backend-code-reviewer`
- `skills/frontend-code-reviewer`
- `skills/fastapi-agents`

## Scaffolds

Use `scripts/scaffold_feature.py` to create starter structure for new features. The script creates
files and TODO checklists only; it does not register routers, edit frontend routes, add permissions,
or implement business logic.

Examples:

```powershell
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run backend audit-log --with-model
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run frontend audit-log --route /admin/audit-log
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run full-stack audit-log --route /admin/audit-log --with-model
```

Use `--dry-run` first when exploring paths.

Use `scripts/bootstrap_new_app.py` to preview or apply one-time new-app identity changes. It requires
an exact clean source snapshot, previews by default, uses a rollback-capable transaction for
captured write failures, and records per-application provenance.

Example:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows."
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows." --write
```
