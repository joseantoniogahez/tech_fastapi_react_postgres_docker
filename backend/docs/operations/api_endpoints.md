# API Endpoints

For implementation rules and extension workflows, see `../backend_playbook.md`.

All routes are versioned under `/v1`.

## Global Conventions

- Bearer auth header: `Authorization: Bearer <access_token>`.
- Standard error payload: `{ detail, status, code, meta?, request_id }`.
- Normalized error responses echo the same `request_id` in the `X-Request-ID` response header.
- Request validation errors are normalized to `400 invalid_input` (not exposed as `422`).
- Write endpoints (`POST`/`PUT`/`PATCH`/`DELETE`) run inside a Unit of Work transaction scope.

## Endpoint Summary

| Method   | Path                                                   | Auth | Permission                | Main Request Contract                                       | Success Response                   | Common Error Statuses                    |
| -------- | ------------------------------------------------------ | ---- | ------------------------- | ----------------------------------------------------------- | ---------------------------------- | ---------------------------------------- |
| `GET`    | `/v1/health`                                           | No   | No                        | No body                                                     | `200` `{ "status": "ok" }`         | -                                        |
| `POST`   | `/v1/token`                                            | No   | No                        | `application/x-www-form-urlencoded` (`username`,`password`) | `200` bearer token                 | `400`, `401`, `403`, `500`               |
| `POST`   | `/v1/users/register`                                   | No   | No                        | JSON `RegisterUserRequest`                                  | `201` `AuthenticatedUserResponse`  | `400`, `409`, `500`                      |
| `GET`    | `/v1/users/me`                                         | Yes  | No                        | No body                                                     | `200` `AuthenticatedUserResponse`  | `401`, `403`, `500`                      |
| `PATCH`  | `/v1/users/me`                                         | Yes  | No                        | JSON `UpdateCurrentUserRequest`                             | `200` `AuthenticatedUserResponse`  | `400`, `401`, `403`, `409`, `500`        |
| `GET`    | `/v1/rbac/roles`                                       | Yes  | `roles:manage`            | No body                                                     | `200` `RBACRole[]`                 | `401`, `403`, `500`                      |
| `GET`    | `/v1/rbac/permissions`                                 | Yes  | `role_permissions:manage` | No body                                                     | `200` `RBACPermission[]`           | `401`, `403`, `500`                      |
| `GET`    | `/v1/rbac/users`                                       | Yes  | `users:manage`            | No body                                                     | `200` `AdminUserResponse[]`        | `401`, `403`, `500`                      |
| `GET`    | `/v1/rbac/users/{user_id}`                             | Yes  | `users:manage`            | Path `user_id`                                              | `200` `AdminUserResponse`          | `400`, `401`, `403`, `404`, `500`        |
| `GET`    | `/v1/rbac/users/{user_id}/roles`                       | Yes  | `user_roles:manage`       | Path `user_id`                                              | `200` `AssignedRole[]`             | `400`, `401`, `403`, `404`, `500`        |
| `GET`    | `/v1/rbac/roles/{role_id}/users`                       | Yes  | `user_roles:manage`       | Path `role_id`                                              | `200` `AssignedUser[]`             | `400`, `401`, `403`, `404`, `500`        |
| `POST`   | `/v1/rbac/users`                                       | Yes  | `users:manage`            | JSON `CreateAdminUserRequest`                               | `201` `AdminUserResponse`          | `400`, `401`, `403`, `404`, `409`, `500` |
| `PUT`    | `/v1/rbac/users/{user_id}`                             | Yes  | `users:manage`            | Path `user_id` + JSON `UpdateAdminUserRequest`              | `200` `AdminUserResponse`          | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/v1/rbac/users/{user_id}`                             | Yes  | `users:manage`            | Path `user_id`                                              | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `POST`   | `/v1/rbac/roles`                                       | Yes  | `roles:manage`            | JSON `CreateRoleRequest`                                    | `201` `RBACRole`                   | `400`, `401`, `403`, `409`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}`                             | Yes  | `roles:manage`            | Path `role_id` + JSON `UpdateRoleRequest`                   | `200` `RBACRole`                   | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/v1/rbac/roles/{role_id}`                             | Yes  | `roles:manage`            | Path `role_id`                                              | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | Yes  | `roles:manage`            | Path `role_id` + `parent_role_id`                           | `204` no body                      | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | Yes  | `roles:manage`            | Path `role_id` + `parent_role_id`                           | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | Yes  | `role_permissions:manage` | Path IDs + JSON `SetRolePermissionRequest`                  | `200` `RBACRolePermission`         | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | Yes  | `role_permissions:manage` | Path `role_id` + `permission_id`                            | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/users/{user_id}/roles/{role_id}`             | Yes  | `user_roles:manage`       | Path `user_id` + `role_id`                                  | `200` `UserRoleAssignmentResponse` | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/v1/rbac/users/{user_id}/roles/{role_id}`             | Yes  | `user_roles:manage`       | Path `user_id` + `role_id`                                  | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |

Protected rows (`Permission != No`) are contract-checked by
`tests/routers/test_authorization_policy_coverage.py`.

## Read Access Classification

This table classifies each `GET` endpoint as `public`, `authenticated`, or `permission`.

| Method | Path                             | Access Level    | Permission                |
| ------ | -------------------------------- | --------------- | ------------------------- |
| `GET`  | `/v1/health`                     | `public`        | No                        |
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
