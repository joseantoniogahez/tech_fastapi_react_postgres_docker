# Backend Docs Index

This folder is the canonical backend documentation set. It is organized for three audiences:

- AI assistant execution
- human reviewer onboarding
- change requester workflows

## Core Playbook

- `backend_playbook.md`: single source of truth for architecture map, mandatory engineering rules, delivery workflows, AI protocol, and reviewer approval checklist.
- `foundation_status.md`: canonical snapshot of current backend foundation state, guardrails, and required validation gates.

## Canonical Runtime Contracts

- `operations/api_endpoints.md`: endpoint catalog, auth requirements, permission mapping, and success/error status expectations.
- `operations/authentication.md`: authentication flow, bootstrap process, and account update policy.
- `operations/authorization_matrix.md`: canonical permission matrix and read-access policy inventory.
- `operations/error_mapping.md`: normalized error payload and domain-to-HTTP status mapping.

## Architecture Annexes

- `architecture/clean_architecture_ports_adapters.md`: feature ownership and dependency direction.
- `architecture/dependency_injection.md`: dependency providers and request-scoped wiring rules.
- `architecture/unit_of_work.md`: transaction boundary behavior and rollback/commit policy.
- `architecture/openapi_documentation.md`: OpenAPI metadata split and naming conventions.
- `architecture/router_registration.md`: dynamic router registration and registration workflow.

## Request Templates

- `templates/feature_request.md`
- `templates/integration_request.md`
- `templates/code_change_request.md`

## Role-Based Reading Order

### AI Assistant Execution (Mandatory)

1. `backend_playbook.md`
1. `foundation_status.md`
1. `operations/api_endpoints.md`
1. `operations/authorization_matrix.md`
1. `operations/error_mapping.md`
1. Relevant architecture annex document(s) for the change.

### Human Reviewer Onboarding

1. `backend_playbook.md`
1. `foundation_status.md`
1. `operations/api_endpoints.md`
1. `operations/authentication.md`
1. `operations/authorization_matrix.md`
1. Relevant architecture annex document(s) touched by the PR.

### Change Requester Workflow

1. Pick one template from `templates/`.
1. Fill every section with concrete acceptance criteria and required tests.
1. Cross-check constraints in `backend_playbook.md` before submitting the request.
