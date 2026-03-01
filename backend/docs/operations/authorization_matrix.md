# Authorization Matrix

Canonical permission definitions live in `app/const/permission.py`.
Permission IDs must follow `<resource>:<action>` using lowercase letters, numbers, and underscores.

## Permission Catalog

| Permission                | Name                         | Resource           | Action |
| ------------------------- | ---------------------------- | ------------------ | ------ |
| `books:create`            | Create books                 | `books`            | create |
| `books:update`            | Update books                 | `books`            | update |
| `books:delete`            | Delete books                 | `books`            | delete |
| `roles:manage`            | Manage roles                 | `roles`            | manage |
| `role_permissions:manage` | Manage role permissions      | `role_permissions` | manage |
| `user_roles:manage`       | Manage user role assignments | `user_roles`       | manage |

## Protected Endpoint Inventory

Permission policies are enforced by `app/dependencies/authorization.py` and mapped in
`app/dependencies/authorization_books.py` and `app/dependencies/authorization_rbac.py`.
This table is a contract: `tests/routers/test_authorization_policy_coverage.py` verifies it
against the live router dependency graph.

| Method   | Path                                                | Permission                | Required Scope | Dependency Alias              |
| -------- | --------------------------------------------------- | ------------------------- | -------------- | ----------------------------- |
| `POST`   | `/books/`                                           | `books:create`            | `any`          | `BookCreateAuth`              |
| `PUT`    | `/books/{id}`                                       | `books:update`            | `any`          | `BookUpdateAuth`              |
| `DELETE` | `/books/{id}`                                       | `books:delete`            | `any`          | `BookDeleteAuth`              |
| `GET`    | `/rbac/roles`                                       | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `GET`    | `/rbac/permissions`                                 | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `POST`   | `/rbac/roles`                                       | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `PUT`    | `/rbac/roles/{role_id}`                             | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `DELETE` | `/rbac/roles/{role_id}`                             | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `PUT`    | `/rbac/roles/{role_id}/permissions/{permission_id}` | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `DELETE` | `/rbac/roles/{role_id}/permissions/{permission_id}` | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `PUT`    | `/rbac/users/{user_id}/roles/{role_id}`             | `user_roles:manage`       | `any`          | `RBACUserRoleAdminAuth`       |
| `DELETE` | `/rbac/users/{user_id}/roles/{role_id}`             | `user_roles:manage`       | `any`          | `RBACUserRoleAdminAuth`       |

## Permission Scope Semantics

Scopes are ordered from narrowest to broadest:

- `own`
- `tenant`
- `any`

Deterministic evaluation rules:

- Required `any`: only granted `any` passes.
- Required `tenant`: granted `tenant` with tenant match, or granted `any`.
- Required `own`: granted `own` with owner match, granted `tenant` with owner or tenant match, or granted `any`.
- Missing owner/tenant context for scope-dependent checks is treated as deny.

## Read Endpoint Access Policy

Canonical read-access policy definitions live in `app/const/permission.py` as
`READ_ACCESS_POLICY_CATALOG`.
This table is a contract: `tests/routers/test_authorization_policy_coverage.py` verifies it
against both the live router dependency graph and the catalog constants.

| Method | Path                | Access Level    | Permission                |
| ------ | ------------------- | --------------- | ------------------------- |
| `GET`  | `/health`           | `public`        | No                        |
| `GET`  | `/users/me`         | `authenticated` | No                        |
| `GET`  | `/authors/`         | `public`        | No                        |
| `GET`  | `/books/`           | `public`        | No                        |
| `GET`  | `/books/published`  | `public`        | No                        |
| `GET`  | `/books/{id}`       | `public`        | No                        |
| `GET`  | `/rbac/roles`       | `permission`    | `roles:manage`            |
| `GET`  | `/rbac/permissions` | `permission`    | `role_permissions:manage` |

## Base Role Catalog (Bootstrap)

Seed source: `utils/rbac_bootstrap.py`

| Role          | Base Permissions                                                                                               |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| `admin_role`  | `books:create`, `books:update`, `books:delete`, `roles:manage`, `role_permissions:manage`, `user_roles:manage` |
| `reader_role` | none (read access behavior is controlled per endpoint)                                                         |

## Notes

- Permission checks are evaluated after bearer token validation.
- Scope checks are evaluated in `app/services/auth.py` via `user_has_permission`.
- Router-level scope/context wiring is defined in `app/dependencies/authorization.py`.
- Read endpoints are classified as exactly one of `public`, `authenticated`, or `permission`.
- Missing permission returns `403 forbidden` with `meta.permission_id`.
- OpenAPI endpoint docs for protected routes live in `app/openapi/books.py` and `app/openapi/rbac.py`.
- Bootstrap command is idempotent: `python -m utils.rbac_bootstrap`.
