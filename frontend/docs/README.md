# Frontend Docs Index

This folder is the canonical frontend documentation set. It is organized for three audiences:

- AI assistant execution
- human reviewer onboarding
- change requester workflows

## Core Playbook

- `frontend_playbook.md`: single source of truth for architecture, non-negotiable rules, AI operating protocol, and reviewer checklist.

## Canonical Runtime Contracts

- `operations/route_inventory.md`: canonical route inventory and access-policy ownership.
- `operations/api_contract_sync.md`: OpenAPI sync workflow and drift-prevention contract.
- `operations/api_consumer_matrix.md`: frontend endpoint consumer and error-contract inventory.
- `operations/mutation_policy.md`: mutation retry and invalidation policy contracts.
- `operations/runtime_config.md`: runtime environment schema and fail-fast behavior contract.
- `operations/browser_security_baseline.md`: browser security policy baseline and enforcement ownership.
- `operations/dependency_policy.md`: dependency audit thresholds and supply-chain gate rules.
- `operations/observability_events.md`: structured observability event schema and redaction rules.
- `operations/runtime_error_pipeline.md`: global runtime error capture and diagnostics contract.
- `operations/support_diagnostics_runbook.md`: incident triage flow and frontend error taxonomy.
- `operations/e2e_smoke_suite.md`: deterministic e2e smoke scenarios and execution contracts.
- `operations/accessibility_gate.md`: automated accessibility baseline and review rules.
- `operations/performance_budget.md`: bundle-size budgets and fail-on-regression gate.

## Foundation Status

- `foundation_status.md`: canonical snapshot of current frontend foundation state, active guardrails, and required validation gates.

## Request Templates

- `templates/feature_request.md`
- `templates/integration_request.md`
- `templates/code_change_request.md`

These templates are designed for developers to request concrete AI-driven changes and make review expectations explicit.

## Role-Based Reading Order

### AI Assistant Execution (Mandatory)

1. `frontend_playbook.md`
1. Relevant operation contract document(s) touched by the request.
1. `foundation_status.md`
1. The completed request template in `templates/`.

### Human Reviewer Onboarding

1. `frontend_playbook.md`
1. `foundation_status.md`
1. Operation contracts impacted by the PR.
1. Request template used in the change request.

### Change Requester Workflow

1. Pick one template from `templates/`.
1. Fill every section with explicit scope, constraints, and validation commands.
1. Reference the exact frontend docs/contracts the AI must follow.
1. Submit the completed template as the prompt/request body.
