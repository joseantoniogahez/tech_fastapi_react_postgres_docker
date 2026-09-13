# Application Backlog Item Plan: `{ITEM-ID}`

Use this template only after a derived application has activated the
[conditional backlog lifecycle](../backlog_tracking.md). Do not instantiate it to populate this
starter kit with example or speculative work.

## Record Control

- Canonical backlog path:
- Item ID and title:
- Status: `Pending` / `In Progress` / `Blocked` / `Implemented` / `Done`
- Application-defined type/priority, if any:
- Owner and required reviewers:
- Branch/commit or immutable revision:
- Created/updated UTC:
- Authorization or approval reference:

## Objective And Starting Evidence

- User or operational outcome:
- Current verified behavior:
- Gap and evidence:
- Observable success measure:

## Scope

### Included

-

### Excluded And Protected

-

## Dependencies, Decisions, And Risks

- Predecessors and external dependencies:
- Closed decisions and links:
- Open questions that materially affect delivery:
- Risks, mitigations, and stop conditions:
- Shared-file ownership or coordination:

## Acceptance Criteria

- [ ] Observable behavior meets the stated outcome.
- [ ] Required tests and documentation are synchronized.
- [ ] Required validation evidence is recorded below.
- [ ] Mandatory approvals are recorded or explicitly not applicable.
- [ ] Rollback and resumption information matches the delivered state.

## Affected Contracts

| Surface                            | Current contract or path | Expected change/review |
| ---------------------------------- | ------------------------ | ---------------------- |
| Runtime/API/data                   |                          |                        |
| Auth/RBAC/security/privacy         |                          |                        |
| Frontend/routes/UX/accessibility   |                          |                        |
| Operations/integrations/deployment |                          |                        |
| Tests/generated artifacts          |                          |                        |
| Canonical docs/governance          |                          |                        |

## Work Plan

1.
1.
1.

## Validation And Evidence

| UTC | Command or review | Expected | Actual result | Evidence link/classification |
| --- | ----------------- | -------- | ------------- | ---------------------------- |

- Environment and non-secret profile:
- Skipped gates, reason, owner, and unblock condition:
- Evidence redaction and retention review:
- Rollback validation:

Never mark an unexecuted command as passed or store secret-bearing raw output in this plan.

## Execution Record

Keep this concise; link durable evidence instead of turning the summary backlog into a changelog.

| UTC | Actor | Status or material decision | Evidence | Next safe action |
| --- | ----- | --------------------------- | -------- | ---------------- |

## Pause Or Handoff

Update these fields before every pause or ownership change:

- Current state and completed work:
- Remaining work in dependency order:
- Changed files and contracts:
- Decisions, assumptions, blockers, approvals, and residual risks:
- Last known green commit or immutable revision:
- Exact next safe command:
- Working directory and non-secret environment:
- Expected result and stop condition:
- Unrelated changes and shared-file locks to protect:
- Receiving owner and acknowledgment:

## Completion And Archive

- Delivered outcome:
- Final validation and evidence:
- Skipped validation and rationale:
- Required approvals:
- Residual risk:
- Rollback point:
- Archived-plan path:
- Summary backlog synchronized without implementation chronology: `Yes` / `No`

Use `Implemented` when engineering is complete but a mandatory gate remains. Use `Done` only when no
required acceptance, documentation, validation, review, or approval remains. Move this same file to
the application's declared implemented-plan archive at either state.
