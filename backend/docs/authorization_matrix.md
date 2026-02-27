# Authorization Matrix

Canonical permission definitions live in `app/const/permission.py`.
Permission IDs must follow `<resource>:<action>` using lowercase letters, numbers, and underscores.

## Permission Catalog

| Permission     | Name         | Resource | Action |
| -------------- | ------------ | -------- | ------ |
| `books:create` | Create books | `books`  | create |
| `books:update` | Update books | `books`  | update |
| `books:delete` | Delete books | `books`  | delete |

## Protected Endpoint Inventory

Permission policies are enforced by `app/dependencies/authorization.py` and mapped in
`app/dependencies/authorization_books.py`.
This table is a contract: `tests/routers/test_authorization_policy_coverage.py` verifies it
against the live router dependency graph.

| Method   | Path          | Permission     | Dependency Alias |
| -------- | ------------- | -------------- | ---------------- |
| `POST`   | `/books/`     | `books:create` | `BookCreateAuth` |
| `PUT`    | `/books/{id}` | `books:update` | `BookUpdateAuth` |
| `DELETE` | `/books/{id}` | `books:delete` | `BookDeleteAuth` |

## Read Endpoint Access Policy

Canonical read-access policy definitions live in `app/const/permission.py` as
`READ_ACCESS_POLICY_CATALOG`.
This table is a contract: `tests/routers/test_authorization_policy_coverage.py` verifies it
against both the live router dependency graph and the catalog constants.

| Method | Path               | Access Level    | Permission |
| ------ | ------------------ | --------------- | ---------- |
| `GET`  | `/health`          | `public`        | No         |
| `GET`  | `/users/me`        | `authenticated` | No         |
| `GET`  | `/authors/`        | `public`        | No         |
| `GET`  | `/books/`          | `public`        | No         |
| `GET`  | `/books/published` | `public`        | No         |
| `GET`  | `/books/{id}`      | `public`        | No         |

## Base Role Catalog (Bootstrap)

Seed source: `utils/rbac_bootstrap.py`

| Role          | Base Permissions                                       |
| ------------- | ------------------------------------------------------ |
| `admin_role`  | `books:create`, `books:update`, `books:delete`         |
| `reader_role` | none (read access behavior is controlled per endpoint) |

## Notes

- Permission checks are evaluated after bearer token validation.
- Read endpoints are classified as exactly one of `public`, `authenticated`, or `permission`.
- Missing permission returns `403 forbidden` with `meta.permission_id`.
- OpenAPI endpoint docs for protected routes live in `app/openapi/books.py`.
- Bootstrap command is idempotent: `python -m utils.rbac_bootstrap`.
