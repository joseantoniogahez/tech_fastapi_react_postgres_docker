# Project Skills Catalog

Repository-local skills are task-specific operating modes for AI-assisted work in this starter kit.
They complement `AGENTS.md`; they do not replace the backend or frontend playbooks.

Use `AGENTS.md` as the first orientation point. Then use the skill that matches the task.

## Activation Guidance

When the active Codex environment auto-discovers repository skills, use the matching skill directly.

When a skill is not auto-discovered:

1. Read this catalog.
1. Open the matching `skills/<skill-name>/SKILL.md`.
1. Follow that skill manually while keeping `AGENTS.md` as the root guide.

Do not copy backend or frontend playbook content into skills. Skills should route the agent to the
canonical docs and validation gates.

## Install Skills Into Codex

Preview installation of all project skills:

```powershell
python scripts/install_project_skills.py
```

Preview one skill:

```powershell
python scripts/install_project_skills.py --skill new-app-bootstrapper
```

Apply after reviewing the preview:

```powershell
python scripts/install_project_skills.py --write
```

By default the installer targets `$CODEX_HOME/skills` or `~/.codex/skills` when `CODEX_HOME` is not
set. Use `--dest <path>` for a custom destination. Existing non-matching skills are not overwritten
unless `--force` is passed.

## Skill Matrix

| Skill                        | Use When                                                                                                                                             | Main Docs to Read                                                                                                                            | Typical Validation                                                                                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project-feature-builder`    | A feature touches both backend and frontend, including API, auth/RBAC, OpenAPI, route, UI, tests, or docs.                                           | `AGENTS.md`, backend and frontend playbooks, both foundation status files, affected operation docs, full-stack request template when needed. | Backend tests and coverage, OpenAPI sync/check, frontend check, e2e when auth/routing/error journeys change, frontend build, pre-commit when practical. |
| `backend-capability-builder` | The change is backend-only: endpoint, service, repository, model, migration, auth/RBAC, outbox, integration port, tests, or backend docs.            | `AGENTS.md`, backend playbook, backend foundation status, affected backend operation and architecture docs.                                  | `python -m pytest backend/tests`, backend coverage gate, pre-commit when docs/config/shared files change.                                               |
| `frontend-feature-builder`   | The change is frontend-only: route, page, shared UI, API consumer, auth-gated screen, RBAC UI, query/mutation behavior, a11y, e2e, or frontend docs. | `AGENTS.md`, frontend playbook, frontend foundation status, affected frontend operation docs.                                                | `npm --prefix frontend run check`, `npm --prefix frontend run build`, e2e when auth/routing/error journeys change.                                      |
| `project-reviewer`           | The user asks for a review, readiness check, PR/diff assessment, or risk scan.                                                                       | `AGENTS.md`, changed-file context, affected backend/frontend playbooks and operation docs.                                                   | Review evidence, relevant targeted checks when needed, and explicit validation gaps.                                                                    |
| `new-app-bootstrapper`       | The task turns this starter kit into a named product or previews/applies new-app identity changes.                                                   | `AGENTS.md`, new-project startup docs, bootstrap checklist, new-app request template, root and service READMEs.                              | Bootstrap dry-run, identity diff review, backend tests, frontend check/build, Docker Compose config, pre-commit; e2e when routes/auth/errors change.    |

## Current Skills

### `project-feature-builder`

Full-stack feature delivery for changes that cross backend and frontend boundaries.

Use for:

- user-facing features with backend endpoints and frontend routes,
- API contract changes that require frontend OpenAPI sync,
- auth or RBAC behavior that affects both sides,
- data model changes with visible UI behavior,
- full-stack docs and validation updates.

Do not use for:

- backend-only implementation,
- frontend-only implementation,
- review-only requests.

### `backend-capability-builder`

Backend capability delivery for backend-only behavior.

Use for:

- new backend vertical slices,
- router/service/repository/schema changes,
- SQLAlchemy models and Alembic migrations,
- auth, JWT, RBAC, permissions, scopes, or read-access policy,
- backend integrations, outbox behavior, tests, and backend docs.

Do not use for:

- frontend route or UI work,
- full-stack changes where OpenAPI and frontend consumers move together.

### `frontend-feature-builder`

Frontend feature delivery for frontend-only behavior.

Use for:

- React routes, pages, and shared UI behavior,
- API consumers and frontend contract parsers,
- auth-gated screens and RBAC UI,
- query and mutation behavior,
- accessibility, e2e smoke coverage, runtime config, observability, performance, and frontend docs.

Do not use for:

- backend API implementation,
- database or migration work.

### `project-reviewer`

Review mode for correctness, drift, and readiness checks.

Use for:

- code review,
- readiness review,
- PR or branch risk assessment,
- validation gap analysis,
- docs, contract, auth/RBAC, route, API, migration, security, and test coverage review.

Review output should lead with findings ordered by severity. If no issues are found, say that clearly
and still name residual validation risk.

### `new-app-bootstrapper`

New-project bootstrap workflow for turning this starter kit into a named application.

Use for:

- dry-run or applied identity bootstrap,
- Compose/env/JWT/package/README/UI naming changes,
- new-app request shaping when identity or scope is incomplete,
- separating identity-only bootstrap from follow-up product features.

Do not use for:

- ordinary feature delivery after the app has already been bootstrapped,
- backend-only or frontend-only feature work.

## Adding or Updating Skills

When adding or updating a skill:

1. Keep the skill concise.
1. Point to canonical docs instead of duplicating playbooks.
1. Include trigger cases, workflow, validation, and final report expectations.
1. Update this catalog.
1. Update `AGENTS.md` when the available skill list changes.
1. Validate the skill with the local skill validation tool when available.
