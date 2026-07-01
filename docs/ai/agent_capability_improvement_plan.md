# Agent Capability Improvement Plan

Status date: `2026-06-30`

## Purpose

Improve how future AI agents use this starter kit after it has been copied or bootstrapped into a
new project.

The repository already has enough documentation to guide implementation. This plan focuses on
making the agent capabilities easier to discover, install, activate, and reuse across projects.

## Current Baseline

Already available:

- `AGENTS.md` as the root operating guide.
- `docs/ai/start_new_project.md` for new-project bootstrap workflow.
- `docs/ai/new_app_bootstrap_checklist.md` for identity and validation checklist.
- `docs/ai/templates/*.md` for structured requests.
- Backend and frontend playbooks plus operation contracts.
- Repository-local skills:
  - `skills/project-feature-builder`
  - `skills/backend-capability-builder`
  - `skills/frontend-feature-builder`
  - `skills/project-reviewer`
  - `skills/new-app-bootstrapper`
- Repository scripts:
  - `scripts/bootstrap_new_app.py`
  - `scripts/scaffold_feature.py`
  - `scripts/install_project_skills.py`

Known gap:

- The skills exist locally, but a fresh Codex environment may not auto-discover or install them.
- There is no repository-local catalog explaining when to use each skill.
- There is no plugin packaging yet.
- There is no MCP need yet; local scripts cover the current workflow.

## Guiding Rules

1. Keep canonical architecture docs in `backend/docs/` and `frontend/docs/`.
1. Keep AI workflow docs in `docs/ai/`.
1. Keep skills concise and route back to canonical docs instead of duplicating playbooks.
1. Add a plugin only after local skills and install flow prove useful.
1. Add an MCP only when the agent needs structured access to a live external system or repeated
   repository actions that scripts cannot cover cleanly.

## Phase 1: Skill Catalog and Activation Guide

Goal:

- Make local skills discoverable and easy to activate in a fresh project.

Deliverables:

- [x] Add `skills/README.md`.
- [x] Document each existing skill, trigger cases, required reading, and validation expectations.
- [x] Add manual fallback instructions for agents when skills are not auto-discovered.
- [x] Link `skills/README.md` from `AGENTS.md` and `docs/ai/README.md`.

Acceptance criteria:

- A future assistant can identify the correct local skill without prior chat context.
- A human can see which skill maps to full-stack, backend, frontend, review, and bootstrap work.
- The catalog points to canonical docs and does not duplicate backend/frontend playbooks.

Validation:

- `pre-commit run --files AGENTS.md docs/ai/README.md skills/README.md`

## Phase 2: New App Bootstrapper Skill

Goal:

- Give new-project bootstrap work a dedicated operating mode.

Deliverables:

- [x] Add `skills/new-app-bootstrapper/SKILL.md`.
- [x] Route the skill to:
  - `AGENTS.md`
  - `docs/ai/start_new_project.md`
  - `docs/ai/new_app_bootstrap_checklist.md`
  - `docs/ai/templates/new_app_request.md`
  - root and service READMEs
- [x] Include the dry-run-first rule for `scripts/bootstrap_new_app.py`.
- [x] Include identity surfaces, protected files, validation gates, and final report expectations.
- [x] Add the skill to `AGENTS.md`.
- [x] Add the skill to `skills/README.md`.

Acceptance criteria:

- A future assistant can bootstrap a named app without rereading unrelated feature-delivery docs.
- The skill requires explicit identity details before broad rename work.
- The skill keeps behavior changes separate from identity-only bootstrap.

Validation:

- `quick_validate.py skills/new-app-bootstrapper`
- `pre-commit run --files AGENTS.md skills/README.md skills/new-app-bootstrapper/SKILL.md`

## Phase 3: Project Skill Installer

Goal:

- Make project-local skills portable into the active Codex environment.

Deliverables:

- [x] Add `scripts/install_project_skills.py`.
- [x] Support dry-run by default.
- [x] Support explicit write/apply mode.
- [x] Copy selected or all repository skills into `$CODEX_HOME/skills`.
- [x] Refuse to overwrite an existing non-matching skill unless an explicit force flag is provided.
- [x] Document usage in `skills/README.md` and `docs/ai/README.md`.

Acceptance criteria:

- A user can preview skill installation before writing files.
- A user can install all starter-kit skills with one command.
- Existing user skills are not overwritten accidentally.
- The installer works on Windows paths.

Validation:

- `python -m py_compile scripts/install_project_skills.py`
- Dry-run install all skills.
- Dry-run install one selected skill.
- Invalid skill name fails clearly.
- `pre-commit run --files scripts/install_project_skills.py skills/README.md docs/ai/README.md`

## Phase 4: Plugin Packaging Evaluation

Goal:

- Decide whether a reusable Codex plugin is worth creating after the skill flow is proven.

Decision inputs:

- [ ] Skills are reused in at least one bootstrapped project.
- [ ] Skill install flow is useful but still repetitive.
- [ ] The starter kit is expected to seed multiple repositories.
- [ ] Plugin packaging would reduce setup more than it adds maintenance.

Possible deliverables:

- [ ] Create a personal/local plugin for this starter kit.
- [ ] Package skills and install instructions.
- [ ] Keep canonical docs in the repository; plugin skills should still point back to project docs.
- [ ] Document plugin install/update flow.

Acceptance criteria:

- Plugin usage is optional and does not replace repository-local docs.
- A project can still function with only `AGENTS.md`, `docs/ai/`, scripts, and local skills.
- Plugin packaging does not fork or duplicate backend/frontend playbooks.

Validation:

- Plugin manifest validates.
- Skill validation still passes after packaging.
- A fresh project can use the plugin and still follow repository docs.

## Phase 5: MCP Decision Point

Goal:

- Avoid building an MCP until there is a real integration need.

Do not build an MCP for:

- Reading local docs.
- Running existing local scripts.
- Copying local skills.
- Basic repository scaffolding.

Consider an MCP only when the agent needs structured access to:

- GitHub PRs, issues, checks, or review threads beyond existing GitHub tooling.
- Deployment provider state.
- Runtime logs or observability events.
- A live database inspection workflow.
- A ticketing system such as Linear or Jira.
- A secrets/config provider.

Possible future MCP candidates:

- [ ] Deployment status and release-readiness MCP.
- [ ] Observability/log triage MCP.
- [ ] Database schema inspection MCP for development environments.
- [ ] Project workflow MCP that wraps validated repository scripts.

Acceptance criteria for any MCP:

- The MCP solves a repeated workflow scripts cannot handle well.
- The MCP has a clear security boundary.
- The MCP avoids exposing secrets by default.
- The MCP returns structured, reviewable data.
- The repository docs explain when to use it and when not to.

## Suggested Implementation Order

1. `skills/README.md`
1. `skills/new-app-bootstrapper/SKILL.md`
1. `scripts/install_project_skills.py`
1. Plugin packaging decision
1. MCP decision only after a concrete need appears

## Definition of Done

This improvement track is complete when:

- [x] Local skills have a catalog and activation guide.
- [x] New-app bootstrap has a dedicated skill.
- [x] Users can install project skills into Codex with a dry-run-first script.
- [ ] Plugin packaging has a documented yes/no decision.
- [ ] MCP scope has a documented decision rule.
- [ ] All added skills and scripts validate.
- [ ] `AGENTS.md`, `docs/ai/README.md`, and relevant skill docs are synchronized.
