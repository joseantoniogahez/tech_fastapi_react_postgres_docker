# AI Governance Docs

This folder contains repository-level AI workflow assets that apply across backend and frontend.

Use `AGENTS.md` as the root operating guide. Use these templates when a request needs a structured
scope before implementation.

## New Project Startup

- `start_new_project.md`: practical workflow for turning this starter kit into a named application.
- `template_reuse_contract.md`: immutable-snapshot, one-time bootstrap, provenance, transaction,
  and recovery contract.

## Tooling

- `python_tooling.md`: exact root `.venv` inventory, platform-specific lock contract, accepted
  Windows/Ubuntu runner matrix, clean installation commands, checksums, and audit workflow.
- `release_validation.md`: hosted validation of real services, production images, and a disposable
  application bootstrapped from the selected template snapshot.

## Skills

- `../../skills/README.md`: repository-local skill catalog and manual activation guide.
- `../../scripts/install_project_skills.py`: previews or installs repository-local skills into the
  active Codex skills directory. It validates the complete pack before discovery, writes only when
  `--write` is passed, and restores the whole requested batch after a failed commit.

## Checklists

- `new_app_bootstrap_checklist.md`: canonical checklist for renaming this starter kit into a new
  application.

## Conditional Backlog Lifecycle

- `backlog_tracking.md`: dormant-by-default lifecycle for a derived application that explicitly
  adopts a canonical backlog; it does not create a backlog for this template.
- `templates/backlog_item_plan.md`: durable application item plan with evidence, archive, and exact
  pause/handoff resumption fields.

## Templates

- `templates/full_stack_feature_request.md`: request shape for features that touch both backend and
  frontend.
- `templates/new_app_request.md`: request shape for bootstrapping a new application from this
  starter kit.
- `templates/backlog_item_plan.md`: item plan used only after a derived application activates the
  conditional backlog lifecycle.

## Scaffolds

- `../../scripts/scaffold_feature.py`: creates backend, frontend, or full-stack feature structure
  with TODO checklists. Use `--dry-run` before writing files.
- `../../scripts/bootstrap_new_app.py`: previews or applies new-app identity changes. It writes only
  when `--write` is passed, requires an exact clean source snapshot, attempts whole-batch rollback
  for captured failures, and writes per-application provenance.

Example:

```powershell
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run full-stack audit-log --route /admin/audit-log --with-model
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --source-repository "https://github.com/example/foundation" --source-revision "<commit-or-tag>" --app-name "Example Portal" --description "A portal for example workflows."
.\.venv\Scripts\python.exe scripts\install_project_skills.py --skill new-app-bootstrapper
```

Use `./.venv/bin/python` with POSIX paths on macOS or Linux.
