---
name: backend-code-reviewer
description: Review FastAPI backend changes for correctness, security, regressions, contract drift, missing tests, and validation gaps. Use when a review touches backend routers, services, repositories, schemas, models, migrations, auth, RBAC, integrations, OpenAPI, or backend documentation.
---

# Backend Code Reviewer

## Workflow

1. Read `AGENTS.md`, `backend/docs/backend_playbook.md`, and
   `backend/docs/foundation_status.md`.
1. Inspect the changed files and nearby code, then read only the affected operation and
   architecture documents.
1. For FastAPI or Starlette behavior, invoke `$fastapi-agents`. Continue with repository contracts
   if its deterministic check reports that the official FastAPI skill is unavailable, and record
   that validation gap.
1. Trace changed routes through dependencies, services, repositories or integrations, transaction
   handling, and response/error mapping.
1. Compare observable behavior with API, authentication, authorization, error, OpenAPI, and any
   product contract explicitly declared canonical by a derived application.
1. Inspect focused tests and run the smallest relevant checks needed to prove or disprove findings.
1. Report findings first, ordered by severity, with file and line references. Do not modify code
   unless the user also requests fixes.

## Review Gates

- Confirm protected endpoints use the intended authentication or permission dependency.
- Confirm writes use the documented Unit of Work boundary and repositories do not commit directly.
- Confirm migrations preserve data integrity, constraints, model parity, and the documented
  downgrade or forward-fix strategy.
- Confirm integration failures are normalized, redacted, observable, and tested.
- Confirm router registration, OpenAPI, endpoint inventory, authorization matrix, and error mapping
  stay synchronized.
- Confirm tests cover success, validation, authorization, not-found isolation, failure paths, and
  regression-prone boundaries as applicable.
- Distinguish proven defects from open questions and unexecuted validation.

## Validation And Output

Use the backend gates in `AGENTS.md`, including coverage and OpenAPI sync/check when the public
contract is affected. Output findings by severity, then questions, validation performed and gaps,
and a concise summary. If there are no findings, say so and name the remaining risk.
