# Backend Docs Index

## Operations

- `operations/api_endpoints.md`: full endpoint catalog, auth requirements, permissions, and status codes.
- `operations/authentication.md`: authentication flow, account rules, `curl` examples, and auth-related errors.
- `operations/authorization_matrix.md`: RBAC matrix (permission -> dependency -> protected endpoint).
- `operations/error_mapping.md`: standard error payload and domain-to-HTTP status mapping.

## Architecture

- `architecture/unit_of_work.md`: transaction boundary and rollback/commit policy by use case.
- `architecture/dependency_injection.md`: dependency providers, typed aliases, and test override patterns.
- `architecture/clean_architecture_ports_adapters.md`: DIP with `Protocol` ports, ports/adapters boundaries, composition root, and extension workflow.
- `architecture/router_registration.md`: modular router auto-registration conventions.
- `architecture/openapi_documentation.md`: OpenAPI documentation pattern split into `app/openapi/*`.

## Backlog

- `backlog/backend_structure_backlog.md`: structural review and follow-up prompts for backend cleanup.
- `backlog/backend_backlog.md`: prioritized backend implementation backlog and suggested commits.

## Recommended Reading Order

1. `operations/api_endpoints.md`
1. `operations/authentication.md`
1. `operations/authorization_matrix.md`
1. `operations/error_mapping.md`
1. `architecture/unit_of_work.md`
1. `architecture/dependency_injection.md`
1. `architecture/clean_architecture_ports_adapters.md`
1. `architecture/openapi_documentation.md`
1. `architecture/router_registration.md`
1. `backlog/backend_structure_backlog.md`
1. `backlog/backend_backlog.md`
