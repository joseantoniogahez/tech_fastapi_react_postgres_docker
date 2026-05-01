# AI-Governed Starter Kit Plan

Status date: `2026-05-01`

## Implementation Progress

- Phase 1: `complete`.
  - Added root AI entrypoint: `AGENTS.md`.
  - Included task routing, reading order, non-negotiable rules, documentation update rules,
    validation matrix, delivery workflow, and final response expectations.
  - Deferred `docs/ai/operating_model.md` because `AGENTS.md` is currently sufficient as the single
    orientation point.
- Phase 2: `complete`.
  - Added repository-local skill pack under `skills/`.
  - Added `project-feature-builder`, `backend-capability-builder`, `frontend-feature-builder`, and
    `project-reviewer`.
  - Validated all four skills with `quick_validate.py`.
- Phase 3: `complete`.
  - Added `docs/ai/templates/full_stack_feature_request.md`.
  - Added `docs/ai/templates/new_app_request.md`.
  - Added `docs/ai/README.md` as the repository-level AI templates index.
  - Linked the templates from `AGENTS.md` and `README.md`.
- Phase 4: `complete`.
  - Added `scripts/scaffold_feature.py` with `backend`, `frontend`, and `full-stack` subcommands.
  - Scaffolds create structure and TODO checklists only; they do not register routers, edit routes,
    add permissions, or implement business logic.
  - Linked scaffold usage from `AGENTS.md`, `docs/ai/README.md`, `README.md`, and the initial
    builder skills.
- Phase 5: `complete`.
  - Added `docs/ai/new_app_bootstrap_checklist.md`.
  - Added `scripts/bootstrap_new_app.py` with dry-run default and explicit `--write` apply mode.
  - Linked new-app bootstrap workflow from `AGENTS.md`, `docs/ai/README.md`, `README.md`, and
    `docs/ai/templates/new_app_request.md`.
- Phase 6: `complete`.
  - Added `docs/ai/forward_testing_report.md`.
  - Validated all four skills with `quick_validate.py`.
  - Compiled and dry-run tested `scripts/scaffold_feature.py` and `scripts/bootstrap_new_app.py`.
  - Confirmed dry-runs do not write artifacts and invalid inputs fail with clear errors.
  - Confirmed governance docs reference the expected templates, checklists, scripts, and skills.
- Next phase: Phase 7, iterate from real features.

## Purpose

Convert this FastAPI, React, PostgreSQL, and Docker foundation into a reusable starter kit where
new applications, features, integrations, and reviews can be executed by AI assistance under
explicit project rules.

The goal is not to make the AI "guess better". The goal is to give it a durable operating system:
canonical docs, specialized skills, repeatable scaffolds, and validation gates that define when a
change is done.

## Current Foundation Assessment

The project is ready to begin this work now.

Backend foundation:

- FastAPI, SQLAlchemy async, Alembic, PostgreSQL, JWT auth, RBAC, UoW, outbox, and integration ports.
- Vertical feature slices are documented and already present.
- Backend docs include playbook, foundation status, API inventory, auth, authorization, error mapping,
  DI, UoW, OpenAPI, and router registration rules.
- Backend tests include documentation and authorization contract coverage.

Frontend foundation:

- Vite, React, TypeScript, React Router, TanStack Query, Tailwind, Vitest, Testing Library, Playwright.
- Route composition, API sync, runtime config, auth/session handling, RBAC UI helpers, observability,
  a11y, performance, dependency audit, and e2e smoke gates are already present.
- Frontend docs include playbook, foundation status, route inventory, API consumer matrix, mutation
  policy, runtime config, security, observability, diagnostics, a11y, performance, and templates.

Repository foundation:

- Docker Compose profiles for dev, test, and prod.
- GitHub Actions CI for hooks, backend, and frontend.
- Pre-commit and pre-push checks.
- Root README and service READMEs explain how to run and validate the system.

Conclusion:

- No major library or architecture addition is required before starting.
- The next layer should be AI governance, not more framework surface area.

## Guiding Principles

1. Keep docs as the source of truth.
   Skills should point to canonical docs instead of duplicating them.

1. Use skills as AI operating modes.
   A skill should tell the assistant what to read, what patterns to follow, what files are normally
   touched, what validations to run, and what output to report.

1. Use scripts for repeatable mechanics.
   If a task will be done often and has a preferred shape, create a script or template instead of
   asking the AI to recreate it from memory each time.

1. Let validation gates define "done".
   Features are not complete until the relevant tests, contract checks, docs updates, and builds pass.

1. Do not add libraries speculatively.
   Add emails, queues, object storage, payments, search, background workers, forms, or UI component
   libraries only when a real application feature needs them.

1. Keep the starter kit small but governed.
   The foundation should stay understandable. AI governance should reduce ambiguity, not create a
   second parallel architecture.

## Target Operating Model

Future AI-assisted work should follow this flow:

1. User describes an application, feature, integration, or code change.
1. Assistant identifies the correct workflow:
   - full-stack feature,
   - backend capability,
   - frontend feature,
   - integration,
   - app bootstrap,
   - review.
1. Assistant reads the required project docs for that workflow.
1. Assistant creates or confirms scope, acceptance criteria, touched contracts, protected files, and
   validation gates.
1. Assistant implements the change using existing architecture patterns.
1. Assistant updates tests and docs in the same change when behavior or contracts move.
1. Assistant runs relevant validation commands.
1. Assistant reports files changed, commands run, results, and any residual risk.

## Proposed Repository Artifacts

### 1. AI Operating Model

Add a root-level AI entrypoint:

- `AGENTS.md`

Purpose:

- Give future assistants a single first file to read.
- Summarize repository rules without duplicating every playbook.
- Route the assistant to backend, frontend, full-stack, integration, review, or bootstrap workflows.
- List mandatory docs and validation gates.
- Define how to handle scope, protected files, docs updates, and final reports.

Recommended contents:

- Repository mission.
- Reading order by task type.
- Non-negotiable rules.
- Validation matrix.
- Documentation update rules.
- AI final response requirements.
- Links to backend and frontend playbooks.

### 2. AI Governance Docs

Optional after `AGENTS.md`, if the root file becomes too large:

- `docs/ai/operating_model.md`
- `docs/ai/skill_catalog.md`
- `docs/ai/new_app_bootstrap_checklist.md`
- `docs/ai/feature_delivery_checklist.md`

Purpose:

- Keep reusable AI workflow knowledge in the repo.
- Make future chats self-contained by telling the assistant what to read.
- Avoid repeating context manually.

### 3. Project Skills

Create a small skill pack. Start with four skills.

Skill: `project-feature-builder`

- Use for full-stack features that touch backend and frontend.
- Reads root AI entrypoint, backend playbook, frontend playbook, affected operation docs, and request
  templates.
- Produces backend routes/services/repositories/schemas, frontend routes/pages/API consumers, tests,
  OpenAPI sync, docs updates, and validation report.

Skill: `backend-capability-builder`

- Use for backend-only features, domain capabilities, auth/RBAC changes, new endpoints, migrations,
  outbox use, or integration ports.
- Reads backend playbook, foundation status, API endpoints, auth/authorization/error contracts, and
  relevant architecture annexes.
- Produces vertical feature changes, tests, docs updates, migration changes when needed, and backend
  validation report.

Skill: `frontend-feature-builder`

- Use for frontend-only routes, pages, shared UI behavior, API consumers, auth-gated screens, query
  and mutation flows, accessibility, or e2e smoke updates.
- Reads frontend playbook, foundation status, route inventory, API sync, API consumer matrix,
  mutation/query policy, runtime config, a11y, performance, and relevant templates.
- Produces UI changes, route updates, API consumer updates, tests, docs updates, and frontend
  validation report.

Skill: `project-reviewer`

- Use for code review and readiness review.
- Reads root AI entrypoint plus affected backend/frontend docs.
- Prioritizes correctness, regressions, missing tests, docs drift, contract drift, auth/RBAC errors,
  security issues, and validation gaps.
- Produces findings first, then open questions, then concise summary.

Later skills:

- `new-app-bootstrapper`
- `integration-builder`
- `rbac-policy-designer`
- `openapi-contract-maintainer`
- `release-readiness-reviewer`

### 4. Scaffolds and Scripts

Add scripts only when a workflow repeats enough to justify deterministic support.

Candidate scripts:

- Backend feature scaffold:

  - create `app/features/<feature>/router.py`,
  - create service, repository, schemas, optional models,
  - create test placeholders,
  - remind assistant to register router and update docs.

- Frontend route scaffold:

  - create `src/features/<feature>/<FeaturePage>.tsx`,
  - create test file,
  - add route placeholder,
  - remind assistant to update route inventory and a11y coverage when required.

- Full-stack feature scaffold:

  - combine backend and frontend scaffolds,
  - prepare OpenAPI sync step,
  - create a local checklist for affected docs and gates.

- New application bootstrap script:

  - rename project identifiers,
  - update Compose project names,
  - update DB names,
  - update JWT issuer/audience defaults,
  - update package metadata,
  - update README title and app description,
  - verify `.env_examples` values.

Important:

- Scaffolds should create structure, not business logic.
- Generated files must still follow playbooks and pass tests.

### 5. Request Templates

Existing backend and frontend templates are good. Add one root full-stack template:

- `docs/ai/templates/full_stack_feature_request.md`

Recommended sections:

- Problem and goal.
- Scope in/out.
- Backend API/data/auth impact.
- Frontend route/state/UX impact.
- Acceptance criteria.
- Required docs to read.
- Allowed and protected files.
- Required tests.
- Required validation commands.
- Expected final report.

Also add a new-app template:

- `docs/ai/templates/new_app_request.md`

Recommended sections:

- App name and domain.
- Branding and terminology.
- Initial roles and permissions.
- Initial routes.
- Initial data model.
- External integrations.
- Deployment expectations.
- Validation gates.

## Validation Matrix

Backend-only change:

- `python -m pytest backend/tests`
- `python -m pytest backend/tests --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=100`
- `pre-commit run --all-files` when docs, hooks, formatting, Docker, or shared config changed.

Frontend-only change:

- `npm --prefix frontend run check`
- `npm --prefix frontend run test:e2e:ci` when auth, routing, or error journeys change.
- `npm --prefix frontend run build`

Full-stack change:

- Backend validation commands.
- `npm --prefix frontend run openapi:sync` or `openapi:check` depending on whether API changed.
- Frontend validation commands.
- `pre-commit run --all-files` before push-level confidence.

Documentation-only change:

- Relevant documentation contract tests.
- `pre-commit run --files <changed-docs>` or full pre-commit when practical.

New app bootstrap:

- Docker Compose config validation.
- Backend tests.
- Frontend check and build.
- Smoke e2e after app-level route/auth changes.

## Architecture and Library Decisions

Do now:

- Add AI operating model docs.
- Add initial skills.
- Add root full-stack and new-app request templates.
- Add scaffolds only for repeated structure.
- Use existing gates as the default definition of done.

Defer until a real app needs it:

- Background worker runtime.
- Message broker.
- Email provider.
- Object/file storage provider.
- Search engine.
- Payment provider.
- UI component library.
- Form library.
- Internationalization runtime beyond the existing text catalog pattern.
- Feature flag service.
- Multi-tenant data isolation.
- Deployment-specific infrastructure modules.

Decision rule:

- Add a dependency only when it supports a current acceptance criterion.
- Prefer adapters/ports first when the concrete provider is not yet known.
- Document the decision in the relevant backend/frontend operation or architecture doc.

## Phased Roadmap

### Phase 1: AI Governance Entry Point

Goal:

- Make future chats self-orienting.

Deliverables:

- Add `AGENTS.md`.
- Add `docs/ai/operating_model.md` if `AGENTS.md` needs more detail.
- Add a validation matrix and reading order by task type.

Acceptance criteria:

- A fresh assistant can read one root file and know where to go next.
- Backend, frontend, full-stack, review, and new-app workflows are routed clearly.
- No existing backend/frontend docs are duplicated unnecessarily.

### Phase 2: Initial Skill Pack

Goal:

- Turn the docs into reusable AI operating modes.

Deliverables:

- `project-feature-builder`
- `backend-capability-builder`
- `frontend-feature-builder`
- `project-reviewer`

Acceptance criteria:

- Each skill has a concise `SKILL.md`.
- Each skill points to canonical project docs.
- Each skill defines expected workflow, validation, and final report.
- Skills are validated with the skill validation tool.

### Phase 3: Full-Stack Request Templates

Goal:

- Make user requests structured enough for reliable AI execution.

Deliverables:

- Root full-stack feature request template.
- New app bootstrap request template.
- Update docs index or README references if needed.

Acceptance criteria:

- A user can fill one template and get a scoped AI task.
- Template explicitly covers backend, frontend, data, auth/RBAC, UX, tests, docs, and validation.

### Phase 4: Scaffolds

Goal:

- Reduce repetitive setup and improve consistency.

Deliverables:

- Backend feature scaffold script or template.
- Frontend route/page scaffold script or template.
- Optional full-stack scaffold wrapper.

Acceptance criteria:

- Generated structure matches existing project architecture.
- Scripts do not create business logic that should be designed case by case.
- Generated placeholders make required docs/tests obvious.

### Phase 5: New App Bootstrap Workflow

Goal:

- Make this repo reusable as a foundation for new applications.

Deliverables:

- New app checklist.
- New app request template.
- Optional bootstrap script.

Acceptance criteria:

- App identity can be changed consistently.
- Compose names, env examples, JWT metadata, package names, README, and initial UI naming are handled.
- Validation commands prove the renamed app still works.

### Phase 6: Forward Testing

Goal:

- Verify that the AI governance layer works on realistic tasks.

Test scenarios:

- Add a simple backend-only capability.
- Add a frontend-only authenticated page.
- Add a small full-stack CRUD feature with RBAC.
- Review a deliberately imperfect change.
- Bootstrap a new app identity from the template.

Acceptance criteria:

- The assistant follows the right docs without manual re-explanation.
- It updates contracts/docs when required.
- It runs the expected gates.
- Review mode catches meaningful risks and missing tests.

### Phase 7: Iterate From Real Features

Goal:

- Improve only where actual use shows friction.

Iteration triggers:

- The assistant repeatedly forgets a doc.
- The assistant repeats boilerplate that could be scaffolded.
- A validation gap allows a regression.
- A new app requires a recurring integration.
- Review comments reveal ambiguous architecture rules.

Expected response:

- Update the relevant skill, template, doc, or script.
- Avoid broad rewrites unless the failure mode is systemic.

## Definition of Done for AI-Governed Starter Kit v1

The starter kit reaches v1 when:

- `AGENTS.md` exists and gives future assistants a clear entrypoint.
- Initial skill pack exists and validates.
- Full-stack and new-app request templates exist.
- Validation matrix is documented.
- At least one realistic feature has been delivered using the new workflow.
- At least one review has been performed using `project-reviewer`.
- The repository still passes backend, frontend, and CI-equivalent gates.

## Suggested First Implementation Order

1. Create `AGENTS.md`.
1. Create `docs/ai/operating_model.md` only if needed.
1. Create `project-feature-builder`.
1. Create `backend-capability-builder`.
1. Create `frontend-feature-builder`.
1. Create `project-reviewer`.
1. Add full-stack feature request template.
1. Add new-app request template.
1. Use the skills on one small real feature.
1. Add scaffolds only after the first repeated pattern is clear.

## Prompt for Future Chats

Use this when starting a new chat:

```text
Read AI_GOVERNED_STARTER_KIT_PLAN.md first. Then continue the AI-governed starter kit work from
the next incomplete phase. Use the existing backend and frontend docs as canonical source of truth.
```
