# AI Governance Docs

This folder contains repository-level AI workflow assets that apply across backend and frontend.

Use `AGENTS.md` as the root operating guide. Use these templates when a request needs a structured
scope before implementation.

## Checklists

- `new_app_bootstrap_checklist.md`: canonical checklist for renaming this starter kit into a new
  application.

## Reports

- `forward_testing_report.md`: latest controlled forward test of the AI governance workflow.

## Templates

- `templates/full_stack_feature_request.md`: request shape for features that touch both backend and
  frontend.
- `templates/new_app_request.md`: request shape for bootstrapping a new application from this
  starter kit.

## Scaffolds

- `../../scripts/scaffold_feature.py`: creates backend, frontend, or full-stack feature structure
  with TODO checklists. Use `--dry-run` before writing files.
- `../../scripts/bootstrap_new_app.py`: previews or applies new-app identity changes. It writes only
  when `--write` is passed.

Example:

```powershell
python scripts/scaffold_feature.py full-stack audit-log --route /admin/audit-log --with-model --dry-run
python scripts/bootstrap_new_app.py --app-name "Example Portal" --description "A portal for example workflows."
```
