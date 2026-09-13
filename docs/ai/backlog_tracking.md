# Conditional Application Backlog Lifecycle

## Purpose And Dormant Default

This document defines a reusable backlog lifecycle for an application derived from this starter
kit. It is dormant in the template: this repository intentionally has no canonical application
backlog and this document does not create one.

The lifecycle activates only when a derived application explicitly declares all of the following in
its root governance documentation:

- the canonical summary backlog path;
- the pending-plan and implemented-plan archive paths;
- the item-ID and optional priority conventions chosen by that application;
- the owner authorized to change status and the required reviewers;
- the evidence location and retention policy.

Do not infer activation from this guide, create placeholder items, or copy an example backlog into a
new application. Add only work representing an approved, concrete application need.

## Required Artifacts After Activation

An adopting application declares paths for these roles without changing their ownership boundary:

- **Summary backlog:** a concise index of real items and their current status.
- **Pending plan directory:** the durable plan for every item that is ready, active, or blocked.
- **Implemented plan archive:** the same plan moved after engineering reaches `Implemented` or the
  item reaches `Done`.
- **Plan template:** [backlog item plan](templates/backlog_item_plan.md).
- **Canonical contracts:** affected backend, frontend, product, operational, and governance docs.

The summary backlog is an index, not a changelog. Keep only the application-defined ID, concise
outcome, current owner, current status, optional application-defined priority, and plan link. Put
scope, decisions, commands, results, file lists, pause notes, and chronology in the item plan or its
linked evidence.

## Status Lifecycle

| Status        | Meaning                                                                                                   | Required record                                                                  |
| ------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `Pending`     | identified or queued work that is not authorized or not ready to execute                                  | concise summary entry; draft plan when useful                                    |
| `In Progress` | an owner has activated executable work and required work remains                                          | plan in the pending directory with scope, evidence, and resumption point         |
| `Blocked`     | a concrete dependency, decision, approval, environment, or external state prevents safe progress          | blocker, owner, attempts, unblock condition, and next review in the pending plan |
| `Implemented` | engineering, docs, and targeted validation are complete, but a mandatory external or release gate remains | archived plan with implementation evidence and the exact missing gate            |
| `Done`        | every acceptance criterion, required validation, documentation update, review, and approval is complete   | archived closeout plan and retained evidence                                     |

Allowed transitions:

```text
Pending -> In Progress -> Implemented -> Done
                 |             |
                 +-> Blocked <-+
Blocked -> In Progress
Implemented -> In Progress (rework)
Done -> Pending only through an approved reopen decision
```

Moving an item from `Pending` to `In Progress` is its activation point. Before that transition, the
pending plan must name scope and exclusions, acceptance criteria, affected contracts, dependencies,
owner and reviewers, validation gates, evidence destination, rollback boundary, and the exact first
safe action. No active item may exist only as a summary row.

## Execution And Evidence

During work:

1. Keep the plan synchronized with material scope, decision, dependency, or risk changes.
1. Record commands only after execution, with actual result and relevant environment.
1. Link concise retained evidence instead of pasting bulky logs into the backlog.
1. Never store secrets, credentials, personal data, prompts, sensitive URLs, or raw production data
   in backlog artifacts.
1. Keep the summary backlog current without adding chronological notes.

Evidence must distinguish passed, failed, skipped, environmental, and external gates. An item may be
`Implemented` only when every remaining gate has an owner and exact unblock condition. It may be
`Done` only when no required work or approval remains.

## Pause And Handoff

Before every pause or ownership change, update the item plan with:

- current state and completed scope;
- remaining work in dependency order;
- changed files and contracts;
- decisions, assumptions, blockers, approvals, and residual risks;
- commands run and their actual results;
- last known green commit or immutable revision;
- exact next safe command, working directory, expected result, and stop condition;
- unrelated workspace changes and shared-file locks that must be protected.

A conversational summary without the durable resumption fields is not a complete handoff.

## Archive And Completion

Move the same plan from the pending directory to the implemented archive when the item reaches
`Implemented` or `Done`; do not create a second plan or discard its history. The summary backlog
continues to show only current status and the archived plan link.

Before completion, compare delivery against every acceptance criterion, review all changed contract
surfaces routed by `AGENTS.md`, run the required validation matrix, record skipped gates with reasons,
and preserve the rollback and resumption information needed for later rework.
