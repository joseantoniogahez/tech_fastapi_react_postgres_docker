# Backend Docs Index

- `api_endpoints.md`: full endpoint catalog, auth requirements, permissions, and status codes.
- `authentication.md`: authentication flow, account rules, `curl` examples, and auth-related errors.
- `authorization_matrix.md`: RBAC matrix (permission -> dependency -> protected endpoint).
- `error_mapping.md`: standard error payload and domain-to-HTTP status mapping.
- `unit_of_work.md`: transaction boundary and rollback/commit policy by use case.
- `dependency_injection.md`: dependency providers, typed aliases, and test override patterns.
- `clean_architecture_ports_adapters.md`: DIP with `Protocol` ports, ports/adapters boundaries, composition root, and extension workflow.
- `router_registration.md`: modular router auto-registration conventions.
- `openapi_documentation.md`: OpenAPI documentation pattern split into `app/openapi/*`.

## Recommended Reading Order

1. `api_endpoints.md`
1. `authentication.md`
1. `authorization_matrix.md`
1. `error_mapping.md`
1. `unit_of_work.md`
1. `dependency_injection.md`
1. `clean_architecture_ports_adapters.md`
1. `openapi_documentation.md`
1. `router_registration.md`
