# API Endpoints

The API exposes routes at root (`/`).
`API_PATH` only sets FastAPI `root_path` metadata and does not remount routes by itself.

## Global Conventions

- Bearer auth header: `Authorization: Bearer <access_token>`.
- Standard error payload: `{ detail, status, code, meta? }`.
- Request validation errors are normalized to `400 invalid_input` (not exposed as `422`).
- Write endpoints (`POST`/`PUT`/`PATCH`/`DELETE`) execute inside a Unit of Work transaction boundary.
  See `unit_of_work.md` for commit/rollback behavior.

## Endpoint Summary

| Method   | Path               | Auth | Permission     | Main Request Contract                                                                    | Success Response           | Common Error Statuses             |
| -------- | ------------------ | ---- | -------------- | ---------------------------------------------------------------------------------------- | -------------------------- | --------------------------------- |
| `GET`    | `/health`          | No   | No             | No body                                                                                  | `200` `{ "status": "ok" }` | -                                 |
| `POST`   | `/token`           | No   | No             | `application/x-www-form-urlencoded` (`username`, `password`)                             | `200` bearer token         | `400`, `401`, `403`, `500`        |
| `POST`   | `/users/register`  | No   | No             | JSON `RegisterUser`                                                                      | `201` `AuthenticatedUser`  | `400`, `409`, `500`               |
| `GET`    | `/users/me`        | Yes  | No             | No body                                                                                  | `200` `AuthenticatedUser`  | `401`, `403`, `500`               |
| `PATCH`  | `/users/me`        | Yes  | No             | JSON `UpdateCurrentUser`                                                                 | `200` `AuthenticatedUser`  | `400`, `401`, `403`, `409`, `500` |
| `GET`    | `/authors/`        | No   | No             | Optional query: `offset` (`>=0`), `limit` (`1..100`), `sort` in `{name, -name, id, -id}` | `200` `Author[]`           | `400`, `500`                      |
| `GET`    | `/books/`          | No   | No             | Optional query `author_id` (`>=1`)                                                       | `200` `Book[]`             | `400`, `500`                      |
| `GET`    | `/books/published` | No   | No             | No body                                                                                  | `200` `Book[]`             | `500`                             |
| `GET`    | `/books/{id}`      | No   | No             | Path `id` (`>=1`)                                                                        | `200` `Book`               | `400`, `404`, `500`               |
| `POST`   | `/books/`          | Yes  | `books:create` | JSON `AddBook`                                                                           | `201` `Book`               | `400`, `401`, `403`, `500`        |
| `PUT`    | `/books/{id}`      | Yes  | `books:update` | Path `id` + JSON `UpdateBook`                                                            | `200` `Book`               | `400`, `401`, `403`, `404`, `500` |
| `DELETE` | `/books/{id}`      | Yes  | `books:delete` | Path `id`                                                                                | `204` no body              | `400`, `401`, `403`, `500`        |

Protected rows (`Permission != No`) are contract-checked by
`tests/routers/test_authorization_policy_coverage.py`.

## Read Access Classification

This table explicitly classifies every `GET` endpoint as `public`, `authenticated`, or
`permission` and is contract-checked by `tests/routers/test_authorization_policy_coverage.py`.

| Method | Path               | Access Level    | Permission |
| ------ | ------------------ | --------------- | ---------- |
| `GET`  | `/health`          | `public`        | No         |
| `GET`  | `/users/me`        | `authenticated` | No         |
| `GET`  | `/authors/`        | `public`        | No         |
| `GET`  | `/books/`          | `public`        | No         |
| `GET`  | `/books/published` | `public`        | No         |
| `GET`  | `/books/{id}`      | `public`        | No         |

## Domain Notes

### Authentication and user profile

- `POST /token` uses FastAPI `OAuth2PasswordRequestForm`.
- `POST /users/register` normalizes usernames to lowercase and enforces password policy.
- `PATCH /users/me` can update username, password, or both.

See `authentication.md` for examples and error scenarios.

### Books behavior

- `GET /books/` supports optional `author_id` filtering.
- `PUT /books/{id}` returns `404` when the book does not exist.
- `POST /books/` returns `201 Created` when the book is created.
- `DELETE /books/{id}` returns `204 No Content` with an empty body; missing IDs are treated as a no-op.

### Authors behavior

- `GET /authors/` defaults to sorting by `name` ascending.
- `GET /authors/` accepts `sort=name|-name|id|-id` to override ordering.

Valid `Book.status` values:

- `published`
- `draft`
