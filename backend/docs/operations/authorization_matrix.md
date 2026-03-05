# Authorization Matrix

Canonical permission definitions live in `app/authorization/catalog.py`.
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

| Method   | Path                                                   | Permission                | Required Scope | Dependency Alias              |
| -------- | ------------------------------------------------------ | ------------------------- | -------------- | ----------------------------- |
| `POST`   | `/v1/books/`                                           | `books:create`            | `any`          | `BookCreateAuth`              |
| `PUT`    | `/v1/books/{book_id}`                                  | `books:update`            | `any`          | `BookUpdateAuth`              |
| `DELETE` | `/v1/books/{book_id}`                                  | `books:delete`            | `any`          | `BookDeleteAuth`              |
| `GET`    | `/v1/rbac/roles`                                       | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `GET`    | `/v1/rbac/permissions`                                 | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `POST`   | `/v1/rbac/roles`                                       | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `PUT`    | `/v1/rbac/roles/{role_id}`                             | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `DELETE` | `/v1/rbac/roles/{role_id}`                             | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `PUT`    | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `DELETE` | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `PUT`    | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `DELETE` | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `PUT`    | `/v1/rbac/users/{user_id}/roles/{role_id}`             | `user_roles:manage`       | `any`          | `RBACUserRoleAdminAuth`       |
| `DELETE` | `/v1/rbac/users/{user_id}/roles/{role_id}`             | `user_roles:manage`       | `any`          | `RBACUserRoleAdminAuth`       |

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

Canonical read-access policy definitions live in `app/authorization/catalog.py` as
`READ_ACCESS_POLICY_CATALOG`.
This table is a contract: `tests/routers/test_authorization_policy_coverage.py` verifies it
against both the live router dependency graph and the catalog constants.

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

## Base Role Catalog (Bootstrap)

Seed source: `utils/rbac_bootstrap.py`

| Role          | Base Permissions                                                                                               |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| `admin_role`  | `books:create`, `books:update`, `books:delete`, `roles:manage`, `role_permissions:manage`, `user_roles:manage` |
| `reader_role` | none (read access behavior is controlled per endpoint)                                                         |

## Role Composition Rules

- Composition is represented as `child_role -> parent_role` links.
- Effective role permissions are computed as the union of direct and inherited role grants.
- For duplicate permission IDs across the inheritance graph, the broadest scope wins (`own < tenant < any`).
- Cycles are rejected when creating inheritance links.

## Notes

- Permission checks are evaluated after bearer token validation.
- Scope checks are evaluated in `app/services/auth/service.py` via `user_has_permission`.
- Router-level scope/context wiring is defined in `app/dependencies/authorization.py`.
- Read endpoints are classified as exactly one of `public`, `authenticated`, or `permission`.
- Missing permission returns `403 forbidden` with `meta.permission_id`.
- OpenAPI endpoint docs for protected routes live under `app/openapi/books/` and `app/openapi/rbac/`.
- Bootstrap command is idempotent: `python -m utils.rbac_bootstrap`.
