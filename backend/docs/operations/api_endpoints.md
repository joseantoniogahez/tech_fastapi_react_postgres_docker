# API Endpoints

The API exposes routes at root (`/`).
`API_PATH` only sets FastAPI `root_path` metadata and does not remount routes by itself.

## Global Conventions

- Bearer auth header: `Authorization: Bearer <access_token>`.
- Standard error payload: `{ detail, status, code, meta? }`.
- Request validation errors are normalized to `400 invalid_input` (not exposed as `422`).
- Write endpoints (`POST`/`PUT`/`PATCH`/`DELETE`) execute inside a Unit of Work transaction boundary.
  See `../architecture/unit_of_work.md` for commit/rollback behavior.

## Endpoint Summary

| Method   | Path                                                | Auth | Permission                | Main Request Contract                                                                    | Success Response                   | Common Error Statuses                    |
| -------- | --------------------------------------------------- | ---- | ------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------- |
| `GET`    | `/health`                                           | No   | No                        | No body                                                                                  | `200` `{ "status": "ok" }`         | -                                        |
| `POST`   | `/token`                                            | No   | No                        | `application/x-www-form-urlencoded` (`username`, `password`)                             | `200` bearer token                 | `400`, `401`, `403`, `500`               |
| `POST`   | `/users/register`                                   | No   | No                        | JSON `RegisterUserRequest`                                                               | `201` `AuthenticatedUserResponse`  | `400`, `409`, `500`                      |
| `GET`    | `/users/me`                                         | Yes  | No                        | No body                                                                                  | `200` `AuthenticatedUserResponse`  | `401`, `403`, `500`                      |
| `PATCH`  | `/users/me`                                         | Yes  | No                        | JSON `UpdateCurrentUserRequest`                                                          | `200` `AuthenticatedUserResponse`  | `400`, `401`, `403`, `409`, `500`        |
| `GET`    | `/authors/`                                         | No   | No                        | Optional query: `offset` (`>=0`), `limit` (`1..100`), `sort` in `{name, -name, id, -id}` | `200` `AuthorResponse[]`           | `400`, `500`                             |
| `GET`    | `/books/`                                           | No   | No                        | Optional query `author_id` (`>=1`)                                                       | `200` `BookResponse[]`             | `400`, `500`                             |
| `GET`    | `/books/published`                                  | No   | No                        | No body                                                                                  | `200` `BookResponse[]`             | `500`                                    |
| `GET`    | `/books/{book_id}`                                  | No   | No                        | Path `book_id` (`>=1`)                                                                   | `200` `BookResponse`               | `400`, `404`, `500`                      |
| `POST`   | `/books/`                                           | Yes  | `books:create`            | JSON `CreateBookRequest`                                                                 | `201` `BookResponse`               | `400`, `401`, `403`, `500`               |
| `PUT`    | `/books/{book_id}`                                  | Yes  | `books:update`            | Path `book_id` + JSON `UpdateBookRequest`                                                | `200` `BookResponse`               | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/books/{book_id}`                                  | Yes  | `books:delete`            | Path `book_id`                                                                           | `204` no body                      | `400`, `401`, `403`, `500`               |
| `GET`    | `/rbac/roles`                                       | Yes  | `roles:manage`            | No body                                                                                  | `200` `RBACRole[]`                 | `401`, `403`, `500`                      |
| `GET`    | `/rbac/permissions`                                 | Yes  | `role_permissions:manage` | No body                                                                                  | `200` `RBACPermission[]`           | `401`, `403`, `500`                      |
| `POST`   | `/rbac/roles`                                       | Yes  | `roles:manage`            | JSON `CreateRoleRequest`                                                                 | `201` `RBACRole`                   | `400`, `401`, `403`, `409`, `500`        |
| `PUT`    | `/rbac/roles/{role_id}`                             | Yes  | `roles:manage`            | Path `role_id` + JSON `UpdateRoleRequest`                                                | `200` `RBACRole`                   | `400`, `401`, `403`, `404`, `409`, `500` |
| `DELETE` | `/rbac/roles/{role_id}`                             | Yes  | `roles:manage`            | Path `role_id`                                                                           | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/rbac/roles/{role_id}/permissions/{permission_id}` | Yes  | `role_permissions:manage` | Path IDs + JSON `SetRolePermissionRequest`                                               | `200` `RBACRolePermission`         | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/rbac/roles/{role_id}/permissions/{permission_id}` | Yes  | `role_permissions:manage` | Path IDs                                                                                 | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |
| `PUT`    | `/rbac/users/{user_id}/roles/{role_id}`             | Yes  | `user_roles:manage`       | Path `user_id` + `role_id`                                                               | `200` `UserRoleAssignmentResponse` | `400`, `401`, `403`, `404`, `500`        |
| `DELETE` | `/rbac/users/{user_id}/roles/{role_id}`             | Yes  | `user_roles:manage`       | Path `user_id` + `role_id`                                                               | `204` no body                      | `400`, `401`, `403`, `404`, `500`        |

Protected rows (`Permission != No`) are contract-checked by
`tests/routers/test_authorization_policy_coverage.py`.

## Read Access Classification

This table explicitly classifies every `GET` endpoint as `public`, `authenticated`, or
`permission` and is contract-checked by `tests/routers/test_authorization_policy_coverage.py`.

| Method | Path                | Access Level    | Permission                |
| ------ | ------------------- | --------------- | ------------------------- |
| `GET`  | `/health`           | `public`        | No                        |
| `GET`  | `/users/me`         | `authenticated` | No                        |
| `GET`  | `/authors/`         | `public`        | No                        |
| `GET`  | `/books/`           | `public`        | No                        |
| `GET`  | `/books/published`  | `public`        | No                        |
| `GET`  | `/books/{book_id}`  | `public`        | No                        |
| `GET`  | `/rbac/roles`       | `permission`    | `roles:manage`            |
| `GET`  | `/rbac/permissions` | `permission`    | `role_permissions:manage` |

## Domain Notes

### Authentication and user profile

- `POST /token` uses FastAPI `OAuth2PasswordRequestForm`.
- `POST /users/register` normalizes usernames to lowercase and enforces password policy.
- `PATCH /users/me` can update username, password, or both.

See `authentication.md` for examples and error scenarios.

### Books behavior

- `GET /books/` supports optional `author_id` filtering.
- `PUT /books/{book_id}` returns `404` when the book does not exist.
- `POST /books/` returns `201 Created` when the book is created.
- `DELETE /books/{book_id}` returns `204 No Content` with an empty body; missing IDs are treated as a no-op.

### Authors behavior

- `GET /authors/` defaults to sorting by `name` ascending.
- `GET /authors/` accepts `sort=name|-name|id|-id` to override ordering.

### RBAC behavior

- `GET /rbac/roles` returns each role with its current permission grants, including scope.
- `PUT /rbac/roles/{role_id}/permissions/{permission_id}` creates or updates the grant in one operation.
- `DELETE /rbac/roles/{role_id}` also removes existing user-role and role-permission links for that role.

Valid `BookResponse.status` values:

- `published`
- `draft`
