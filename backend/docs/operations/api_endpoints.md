# API Endpoints

For implementation rules and extension workflows, see `../backend_playbook.md`.

All routes are versioned under `/v1`.

## Global Conventions

- Bearer auth header: `Authorization: Bearer <access_token>`.
- Standard error payload: `{ detail, status, code, meta?, request_id }`.
- Normalized error responses echo the same `request_id` in the `X-Request-ID` response header.
- Request validation errors are normalized to `400 invalid_input` (not exposed as `422`).
- OpenAPI HTTP routes exist only in `local`, `test`, and `development`; the operation-level
  `OpenAPI` column means inclusion when that controlled surface is enabled.
- Credentialed CORS uses explicit canonical origins; methods are `GET`, `POST`, `PUT`, `PATCH`,
  `DELETE`, and `OPTIONS`, and request headers are `Accept`, `Authorization`, `Content-Type`, and
  `X-Request-ID`. `X-Request-ID`, numeric quota headers, and `Retry-After` are exposed to browser
  clients.
- Mutating use cases run inside a Unit of Work transaction scope. The transaction requirement is
  determined by the use case, not by its HTTP verb alone.

## Endpoint Summary

| Method   | Path                                                   | Auth | Permission                | OpenAPI | Main Request Contract                                       | Success Response                   | Common Error Statuses                    |
| -------- | ------------------------------------------------------ | ---- | ------------------------- | ------- | ----------------------------------------------------------- | ---------------------------------- | ---------------------------------------- |
| `GET`    | `/v1/audit-log`                                        | Yes  | `audit_logs:read`         | Visible | No body                                                     | `200` `AuditLogEntryResponse[]`    | `401`, `403`, `500`                      |
| `GET`    | `/v1/health`                                           | No   | No                        | Visible | No body                                                     | `200` `{ "status": "ok" }`         | -                                        |
| `GET`    | `/v1/readiness`                                        | No   | No                        | Visible | No body                                                     | `200` `ReadinessResponse`          | `503`                                    |
| `POST`   | `/v1/token`                                            | No   | No                        | Visible | `application/x-www-form-urlencoded` (`username`,`password`) | `200` bearer token                 | `400`, `401`, `403`, `429`, `500`, `503` |
| `POST`   | `/v1/users/register`                                   | No   | No                        | Visible | JSON `RegisterUserRequest`                                  | `201` `AuthenticatedUserResponse`  | `400`, `409`, `429`, `500`, `503`        |
| `GET`    | `/v1/users/me`                                         | Yes  | No                        | Visible | No body                                                     | `200` `AuthenticatedUserResponse`  | `401`, `403`, `500`                      |
| `PATCH`  | `/v1/users/me`                                         | Yes  | No                        | Visible | JSON `UpdateCurrentUserRequest`                             | `200` `AuthenticatedUserResponse`  | `400`, `401`, `403`, `409`, `500`        |
| `GET`    | `/v1/rbac/roles`                                       | Yes  | `roles:manage`            | Visible | No body                                                     | `200` `RBACRole[]`                 | `401`, `403`, `500`                      |
| `GET`    | `/v1/rbac/permissions`                                 | Yes  | `role_permissions:manage` | Visible | No body                                                     | `200` `RBACPermission[]`           | `401`, `403`, `500`                      |
| `GET`    | `/v1/rbac/users`                                       | Yes  | `users:manage`            | Visible | No body                                                     | `200` `AdminUserResponse[]`        | `401`, `403`, `500`                      |
| `GET`    | `/v1/rbac/users/{user_id}`                             | Yes  | `users:manage`            | Visible | Path `user_id`                                              | `200` `AdminUserResponse`          | `400`, `401`, `403`, `404`, `500`        |
| `GET`    | `/v1/rbac/users/{user_id}/roles`                       | Yes  | `user_roles:manage`       | Visible | Path `user_id`                                              | `200` `AssignedRole[]`             | `400`, `401`, `403`, `404`, `500`        |
| `GET`    | `/v1/rbac/roles/{role_id}/users`                       | Yes  | `user_roles:manage`       | Visible | Path `role_id`                                              | `200` `AssignedUser[]`             | `400`, `401`, `403`, `404`, `500`        |
| `POST`   | `/v1/rbac/users`                                       | Yes  | `users:manage`            | Visible | JSON `CreateAdminUserRequest`                               | `201` `AdminUserResponse`          | `400`, `401`, `403`, `404`, `409`, `500` |
| `PUT`    | `/v1/rbac/users/{user_id}`                             | Yes  | `users:manage`            | Visible | Path `user_id` + JSON `UpdateAdminUserRequest`              | `200` `AdminUserResponse`          | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/v1/rbac/users/{user_id}`                             | Yes  | `users:manage`            | Visible | Path `user_id`                                              | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `POST`   | `/v1/rbac/roles`                                       | Yes  | `roles:manage`            | Visible | JSON `CreateRoleRequest`                                    | `201` `RBACRole`                   | `400`, `401`, `403`, `409`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}`                             | Yes  | `roles:manage`            | Visible | Path `role_id` + JSON `UpdateRoleRequest`                   | `200` `RBACRole`                   | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/v1/rbac/roles/{role_id}`                             | Yes  | `roles:manage`            | Visible | Path `role_id`                                              | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | Yes  | `roles:manage`            | Visible | Path `role_id` + `parent_role_id`                           | `204` no body                      | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | Yes  | `roles:manage`            | Visible | Path `role_id` + `parent_role_id`                           | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | Yes  | `role_permissions:manage` | Visible | Path IDs + JSON `SetRolePermissionRequest`                  | `200` `RBACRolePermission`         | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | Yes  | `role_permissions:manage` | Visible | Path `role_id` + `permission_id`                            | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/users/{user_id}/roles/{role_id}`             | Yes  | `user_roles:manage`       | Visible | Path `user_id` + `role_id`                                  | `200` `UserRoleAssignmentResponse` | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/v1/rbac/users/{user_id}/roles/{role_id}`             | Yes  | `user_roles:manage`       | Visible | Path `user_id` + `role_id`                                  | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |

Protected rows (`Permission != No`) are contract-checked by
`tests/routers/test_authorization_policy_coverage.py`.

## Read Access Classification

This table classifies each `GET` endpoint as `public`, `authenticated`, or `permission`.

| Method | Path                             | Access Level    | Permission                |
| ------ | -------------------------------- | --------------- | ------------------------- |
| `GET`  | `/v1/audit-log`                  | `permission`    | `audit_logs:read`         |
| `GET`  | `/v1/health`                     | `public`        | No                        |
| `GET`  | `/v1/readiness`                  | `public`        | No                        |
| `GET`  | `/v1/users/me`                   | `authenticated` | No                        |
| `GET`  | `/v1/rbac/roles`                 | `permission`    | `roles:manage`            |
| `GET`  | `/v1/rbac/permissions`           | `permission`    | `role_permissions:manage` |
| `GET`  | `/v1/rbac/users`                 | `permission`    | `users:manage`            |
| `GET`  | `/v1/rbac/users/{user_id}`       | `permission`    | `users:manage`            |
| `GET`  | `/v1/rbac/users/{user_id}/roles` | `permission`    | `user_roles:manage`       |
| `GET`  | `/v1/rbac/roles/{role_id}/users` | `permission`    | `user_roles:manage`       |

## Domain Notes

### Authentication

- `POST /v1/token` uses FastAPI `OAuth2PasswordRequestForm`.
- `POST /v1/users/register` normalizes usernames and enforces password policy.
- Both public authentication writes are rate-limited before credential or account processing; see
  `rate_limiting.md`.
- `PATCH /v1/users/me` supports username/password updates.
- `POST /v1/users/register`, `GET /v1/users/me`, and `PATCH /v1/users/me` return
  `AuthenticatedUserResponse` with deterministic `permissions` (sorted unique effective permission ids from direct
  and inherited roles).

### RBAC

- `GET /v1/rbac/users` and `GET /v1/rbac/users/{user_id}` expose admin user management views including assigned `role_ids`.
- `POST /v1/rbac/users` creates users with username normalization, password policy enforcement, and optional role assignments.
- `PUT /v1/rbac/users/{user_id}` supports username, password, disabled status, and full role-set replacement updates.
- `DELETE /v1/rbac/users/{user_id}` performs logical deletion only by setting `disabled=true`.
- `GET /v1/rbac/roles` returns effective permissions (direct + inherited) and direct `parent_role_ids`.
- `PUT /v1/rbac/roles/{role_id}/inherits/{parent_role_id}` manages role inheritance.
- `PUT /v1/rbac/roles/{role_id}/permissions/{permission_id}` is an upsert operation.
- `PUT /v1/rbac/roles/{role_id}/permissions/{permission_id}` requires an explicit `scope` in `SetRolePermissionRequest`; omitted scope is rejected as `400 invalid_input`.
- `GET /v1/rbac/users/{user_id}/roles` returns direct user-role assignments.
- `GET /v1/rbac/roles/{role_id}/users` returns direct role-user assignments.
- `DELETE /v1/rbac/roles/{role_id}` also removes related role links and user-role assignments.

### Audit Log

- `GET /v1/audit-log` returns the most recent audit log entries for administrator review.
- Access requires `audit_logs:read`.
- The current feature exposes existing audit rows only; automatic event capture is intentionally out of scope.
