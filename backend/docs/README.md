# Backend Docs Index

## Operations

- `operations/api_endpoints.md`: endpoint catalog, auth requirements, permissions, and status codes.
- `operations/authentication.md`: authentication flow, account rules, and error scenarios.
- `operations/authorization_matrix.md`: RBAC matrix (permission -> dependency -> protected endpoint).
- `operations/error_mapping.md`: standard error payload and domain-to-HTTP status mapping.

## Architecture

- `architecture/unit_of_work.md`: transaction boundary and rollback/commit policy.
- `architecture/dependency_injection.md`: dependency providers, typed aliases, and test overrides.
- `architecture/clean_architecture_ports_adapters.md`: ports/adapters and dependency inversion notes.
- `architecture/router_registration.md`: router registration conventions.
- `architecture/openapi_documentation.md`: OpenAPI metadata conventions.

## Backlog

- `backlog/feature_growth_backlog.md`: neutral backlog for feature-based growth.

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
1. `backlog/feature_growth_backlog.md`
