---
name: fastapi-agents
description: Adapter for the official FastAPI coding-agent skill and this repository's governance rules. Use when Codex implements or reviews FastAPI, Pydantic, dependency injection, streaming, lifecycle, OpenAPI, middleware, security, or Starlette-backed behavior.
---

# FastAPI Agents Adapter

## Resolve The Official Skill

Use the repository-root interpreter to resolve the installed `fastapi` package. The only accepted
official path is `<fastapi-package>/.agents/skills/fastapi/SKILL.md`. Do not copy that skill into
this repository and do not search another environment.

When the path exists, load it first and then apply the overlay below. When it does not exist, stop
official-skill delegation and emit exactly:

```text
FASTAPI_OFFICIAL_SKILL_UNAVAILABLE: the FastAPI distribution in the repository root .venv does not provide .agents/skills/fastapi/SKILL.md; continue only with repository canonical docs and do not upgrade FastAPI solely to obtain the skill.
```

This unavailable result is an accepted adapter state. It is not permission to install or upgrade a
dependency, and it must be reported as a validation limitation.

## Repository Overlay

1. Read `AGENTS.md`, `backend/docs/backend_playbook.md`, and
   `backend/docs/foundation_status.md`.
1. Read affected backend operation and architecture docs. For full-stack work, also read the
   frontend playbook and API contract-sync documentation.
1. Preserve documented routing, service, repository, DI, Unit of Work, authorization, normalized
   error, and OpenAPI contracts.
1. Add or update tests and canonical docs with behavior changes.
1. Run the validation matrix in `AGENTS.md` and report skipped checks and residual risk.

## Safety Boundary

This skill guides coding agents. It does not add an AI agent to the running API, authorize the
third-party `fastapi-agent` package, or select an optional AI capability.
