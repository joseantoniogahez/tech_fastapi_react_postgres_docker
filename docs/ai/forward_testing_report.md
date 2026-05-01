# AI Governance Forward Testing Report

Status date: `2026-05-01`

## Scope

This pass tested the AI-governed starter kit workflow without applying a real feature, writing a
real scaffold, or bootstrapping a new application in place.

Covered areas:

- root AI orientation through `AGENTS.md`,
- repository-local skill pack structure,
- feature scaffold dry-runs,
- new-app bootstrap dry-runs,
- cross-reference consistency between docs, skills, templates, and scripts.

## Commands Run

Skill validation:

```powershell
.\.venv\Scripts\python.exe C:\Users\chepi\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\project-feature-builder
.\.venv\Scripts\python.exe C:\Users\chepi\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\backend-capability-builder
.\.venv\Scripts\python.exe C:\Users\chepi\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\frontend-feature-builder
.\.venv\Scripts\python.exe C:\Users\chepi\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\project-reviewer
```

Script structural validation:

```powershell
.\.venv\Scripts\python.exe -m py_compile scripts\scaffold_feature.py scripts\bootstrap_new_app.py
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --help
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --help
```

Feature scaffold dry-runs:

```powershell
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run backend audit-log --with-model
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run frontend audit-log --route /admin/audit-log
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run full-stack audit-log --route /admin/audit-log --with-model
```

New-app bootstrap dry-runs:

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --app-name "Example Portal" --description "A portal for example workflows."
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --app-name "Example Portal" --slug example-portal --description "A portal for example workflows." --db-name example_main --jwt-issuer example-portal --jwt-audience example-portal-api
```

Safety checks:

```powershell
Test-Path backend\app\features\audit_log
Test-Path frontend\src\features\audit-log
Test-Path docs\ai\scaffolds\audit-log_full_stack_checklist.md
.\.venv\Scripts\python.exe scripts\scaffold_feature.py --dry-run backend 9bad
.\.venv\Scripts\python.exe scripts\bootstrap_new_app.py --app-name "Example Portal" --slug Bad_Slug
```

## Results

- All four skills validated successfully.
- Both scripts compiled successfully.
- Both scripts exposed help output successfully.
- Backend scaffold dry-run produced the expected vertical feature structure and backend checklist.
- Frontend scaffold dry-run produced the expected page, test, and frontend checklist structure.
- Full-stack scaffold dry-run combined backend, frontend, and full-stack checklist outputs.
- New-app bootstrap dry-run found the expected identity surfaces:
  - root README,
  - backend README,
  - `.env_examples`,
  - Compose profiles,
  - backend JWT defaults,
  - frontend package metadata,
  - frontend document title,
  - frontend landing text.
- Dry-runs did not create `audit-log` artifacts.
- Invalid feature names and invalid app slugs failed with clear errors.
- Governance docs reference the expected templates, checklists, scripts, and skills.

## Limitations

- No real feature was implemented.
- No real scaffold files were written.
- No new-app bootstrap was applied with `--write`.
- Backend and frontend runtime tests were not run because no runtime behavior changed.
- Pre-commit hooks were not rerun during this phase; run them before merging the AI governance work.

## Conclusion

The AI governance workflow is ready for a first real feature trial. The next iteration should use
`project-feature-builder` on a small feature and update docs, skills, templates, or scripts only if
the real workflow exposes friction.
