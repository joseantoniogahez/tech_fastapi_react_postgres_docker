# Backend Docs Index

- `api_endpoints.md`: full endpoint catalog, auth requirements, permissions, and status codes.
- `authentication.md`: authentication flow, account rules, `curl` examples, and auth-related errors.
- `authorization_matrix.md`: RBAC matrix (permission -> dependency -> protected endpoint).
- `error_mapping.md`: standard error payload and domain-to-HTTP status mapping.
- `dependency_injection.md`: dependency providers, typed aliases, and test override patterns.
- `router_registration.md`: modular router auto-registration conventions.
- `openapi_documentation.md`: OpenAPI documentation pattern split into `app/openapi/*`.

## Recommended Reading Order

1. `api_endpoints.md`
2. `authentication.md`
3. `authorization_matrix.md`
4. `error_mapping.md`
5. `openapi_documentation.md`
6. `dependency_injection.md`
7. `router_registration.md`
