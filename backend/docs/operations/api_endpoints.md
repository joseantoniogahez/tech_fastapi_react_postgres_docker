# API Endpoints

The API exposes versioned routes under `/v1`.
`API_PATH` only sets FastAPI `root_path` metadata and does not remount routes by itself.

## Versioning Migration Note

- Since 2026-03-05, canonical backend routes are versioned under `/v1`.
- Previous unversioned paths (for example `/token`, `/books`, `/rbac/roles`) are no longer the primary contract.
- Client integrations should call `/v1/*` paths.

## Global Conventions

- Bearer auth header: `Authorization: Bearer <access_token>`.
- Standard error payload: `{ detail, status, code, meta? }`.
- Request validation errors are normalized to `400 invalid_input` (not exposed as `422`).
- Write endpoints (`POST`/`PUT`/`PATCH`/`DELETE`) execute inside a Unit of Work transaction boundary.
  See `../architecture/unit_of_work.md` for commit/rollback behavior.

## Endpoint Summary

| Method   | Path                                                   | Auth | Permission                | Main Request Contract                                                                                                        | Success Response                   | Common Error Statuses                    |
| -------- | ------------------------------------------------------ | ---- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------- |
| `GET`    | `/v1/health`                                           | No   | No                        | No body                                                                                                                      | `200` `{ "status": "ok" }`         | -                                        |
| `POST`   | `/v1/token`                                            | No   | No                        | `application/x-www-form-urlencoded` (`username`, `password`)                                                                 | `200` bearer token                 | `400`, `401`, `403`, `500`               |
| `POST`   | `/v1/users/register`                                   | No   | No                        | JSON `RegisterUserRequest`                                                                                                   | `201` `AuthenticatedUserResponse`  | `400`, `409`, `500`                      |
| `GET`    | `/v1/users/me`                                         | Yes  | No                        | No body                                                                                                                      | `200` `AuthenticatedUserResponse`  | `401`, `403`, `500`                      |
| `PATCH`  | `/v1/users/me`                                         | Yes  | No                        | JSON `UpdateCurrentUserRequest`                                                                                              | `200` `AuthenticatedUserResponse`  | `400`, `401`, `403`, `409`, `500`        |
| `GET`    | `/v1/authors/`                                         | No   | No                        | Optional query: `offset` (`>=0`), `limit` (`1..100`), `sort` in `{name, -name, id, -id}`                                     | `200` `AuthorResponse[]`           | `400`, `500`                             |
| `GET`    | `/v1/books/`                                           | No   | No                        | Optional query: `author_id` (`>=1`), `offset` (`>=0`), `limit` (`1..100`), `sort` in `{id, -id, title, -title, year, -year}` | `200` `BookResponse[]`             | `400`, `500`                             |
| `GET`    | `/v1/books/published`                                  | No   | No                        | No body                                                                                                                      | `200` `BookResponse[]`             | `500`                                    |
| `GET`    | `/v1/books/{book_id}`                                  | No   | No                        | Path `book_id` (`>=1`)                                                                                                       | `200` `BookResponse`               | `400`, `404`, `500`                      |
| `POST`   | `/v1/books/`                                           | Yes  | `books:create`            | JSON `CreateBookRequest`                                                                                                     | `201` `BookResponse`               | `400`, `401`, `403`, `500`               |
| `PUT`    | `/v1/books/{book_id}`                                  | Yes  | `books:update`            | Path `book_id` + JSON `UpdateBookRequest`                                                                                    | `200` `BookResponse`               | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/v1/books/{book_id}`                                  | Yes  | `books:delete`            | Path `book_id`                                                                                                               | `204` no body                      | `400`, `401`, `403`, `500`               |
| `GET`    | `/v1/rbac/roles`                                       | Yes  | `roles:manage`            | No body                                                                                                                      | `200` `RBACRole[]`                 | `401`, `403`, `500`                      |
| `GET`    | `/v1/rbac/permissions`                                 | Yes  | `role_permissions:manage` | No body                                                                                                                      | `200` `RBACPermission[]`           | `401`, `403`, `500`                      |
| `POST`   | `/v1/rbac/roles`                                       | Yes  | `roles:manage`            | JSON `CreateRoleRequest`                                                                                                     | `201` `RBACRole`                   | `400`, `401`, `403`, `409`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}`                             | Yes  | `roles:manage`            | Path `role_id` + JSON `UpdateRoleRequest`                                                                                    | `200` `RBACRole`                   | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/v1/rbac/roles/{role_id}`                             | Yes  | `roles:manage`            | Path `role_id`                                                                                                               | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | Yes  | `roles:manage`            | Path IDs                                                                                                                     | `204` no body                      | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | Yes  | `roles:manage`            | Path IDs                                                                                                                     | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | Yes  | `role_permissions:manage` | Path IDs + JSON `SetRolePermissionRequest`                                                                                   | `200` `RBACRolePermission`         | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | Yes  | `role_permissions:manage` | Path IDs                                                                                                                     | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/v1/rbac/users/{user_id}/roles/{role_id}`             | Yes  | `user_roles:manage`       | Path `user_id` + `role_id`                                                                                                   | `200` `UserRoleAssignmentResponse` | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/v1/rbac/users/{user_id}/roles/{role_id}`             | Yes  | `user_roles:manage`       | Path `user_id` + `role_id`                                                                                                   | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |

Protected rows (`Permission != No`) are contract-checked by
`tests/routers/test_authorization_policy_coverage.py`.

## Read Access Classification

This table explicitly classifies every `GET` endpoint as `public`, `authenticated`, or
`permission` and is contract-checked by `tests/routers/test_authorization_policy_coverage.py`.

| Method | Path                   | Access Level    | Permission                |
| ------ | ---------------------- | --------------- | ------------------------- |
| `GET`  | `/v1/health`           | `public`        | No                        |
| `GET`  | `/v1/users/me`         | `authenticated` | No                        |
| `GET`  | `/v1/authors/`         | `public`        | No                        |
| `GET`  | `/v1/books/`           | `public`        | No                        |
| `GET`  | `/v1/books/published`  | `public`        | No                        |
| `GET`  | `/v1/books/{book_id}`  | `public`        | No                        |
| `GET`  | `/v1/rbac/roles`       | `permission`    | `roles:manage`            |
| `GET`  | `/v1/rbac/permissions` | `permission`    | `role_permissions:manage` |

## Domain Notes

### Authentication and user profile

- `POST /v1/token` uses FastAPI `OAuth2PasswordRequestForm`.
- `POST /v1/users/register` normalizes usernames to lowercase and enforces password policy.
- `PATCH /v1/users/me` can update username, password, or both.

See `authentication.md` for examples and error scenarios.

### Books behavior

- `GET /v1/books/` supports optional `author_id` filtering, pagination (`offset`/`limit`), and deterministic sorting.
- `GET /v1/books/` defaults to sorting by `id` ascending.
- `PUT /v1/books/{book_id}` returns `404` when the book does not exist.
- `POST /v1/books/` returns `201 Created` when the book is created.
- `DELETE /v1/books/{book_id}` returns `204 No Content` with an empty body; missing IDs are treated as a no-op.

### Authors behavior

- `GET /v1/authors/` defaults to sorting by `name` ascending.
- `GET /v1/authors/` accepts `sort=name|-name|id|-id` to override ordering.

### RBAC behavior

- `GET /v1/rbac/roles` returns each role with effective permission grants (direct + inherited), including scope.
- `PUT /v1/rbac/roles/{role_id}/inherits/{parent_role_id}` links role composition (child inherits parent permissions).
- `PUT /v1/rbac/roles/{role_id}/permissions/{permission_id}` creates or updates the grant in one operation.
- `DELETE /v1/rbac/roles/{role_id}` also removes existing user-role, role-permission, and role-inheritance links for that role.

Valid `BookResponse.status` values:

- `published`
- `draft`
