# Authorization Matrix

For implementation rules and extension workflows, see `../backend_playbook.md`.

Canonical permission definitions live in `app/core/authorization/catalog.py`.
Permission IDs follow `<resource>:<action>` with lowercase letters, numbers, and underscores.

## Permission Catalog

| Permission                | Name                         | Resource           | Action |
| ------------------------- | ---------------------------- | ------------------ | ------ |
| `roles:manage`            | Manage roles                 | `roles`            | manage |
| `role_permissions:manage` | Manage role permissions      | `role_permissions` | manage |
| `user_roles:manage`       | Manage user role assignments | `user_roles`       | manage |
| `users:manage`            | Manage users                 | `users`            | manage |

## Protected Endpoint Inventory

Permission policies are enforced by `app/core/authorization/dependencies.py` and
`app/features/rbac/dependencies.py`.
This table is contract-checked by `tests/routers/test_authorization_policy_coverage.py`.

| Method   | Path                                                   | Permission                | Required Scope | Dependency Alias              |
| -------- | ------------------------------------------------------ | ------------------------- | -------------- | ----------------------------- |
| `GET`    | `/v1/rbac/roles`                                       | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `GET`    | `/v1/rbac/permissions`                                 | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `GET`    | `/v1/rbac/users`                                       | `users:manage`            | `any`          | `RBACUserAdminAuth`           |
| `GET`    | `/v1/rbac/users/{user_id}`                             | `users:manage`            | `any`          | `RBACUserAdminAuth`           |
| `POST`   | `/v1/rbac/users`                                       | `users:manage`            | `any`          | `RBACUserAdminAuth`           |
| `PUT`    | `/v1/rbac/users/{user_id}`                             | `users:manage`            | `any`          | `RBACUserAdminAuth`           |
| `DELETE` | `/v1/rbac/users/{user_id}`                             | `users:manage`            | `any`          | `RBACUserAdminAuth`           |
| `POST`   | `/v1/rbac/roles`                                       | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `PUT`    | `/v1/rbac/roles/{role_id}`                             | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `DELETE` | `/v1/rbac/roles/{role_id}`                             | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `PUT`    | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `DELETE` | `/v1/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `roles:manage`            | `any`          | `RBACRoleAdminAuth`           |
| `PUT`    | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `DELETE` | `/v1/rbac/roles/{role_id}/permissions/{permission_id}` | `role_permissions:manage` | `any`          | `RBACRolePermissionAdminAuth` |
| `PUT`    | `/v1/rbac/users/{user_id}/roles/{role_id}`             | `user_roles:manage`       | `any`          | `RBACUserRoleAdminAuth`       |
| `DELETE` | `/v1/rbac/users/{user_id}/roles/{role_id}`             | `user_roles:manage`       | `any`          | `RBACUserRoleAdminAuth`       |
| `GET`    | `/v1/rbac/users/{user_id}/roles`                       | `user_roles:manage`       | `any`          | `RBACUserRoleAdminAuth`       |
| `GET`    | `/v1/rbac/roles/{role_id}/users`                       | `user_roles:manage`       | `any`          | `RBACUserRoleAdminAuth`       |

## Permission Scope Semantics

Scopes are ordered from narrowest to broadest:

- `own`
- `tenant`
- `any`

Deterministic evaluation rules:

- Required `any`: only granted `any` passes.
- Required `tenant`: granted `tenant` (tenant match) or granted `any`.
- Required `own`: granted `own` (owner match), granted `tenant` (owner or tenant match), or granted `any`.
- Missing required owner/tenant context resolves to deny.

## Conditional Policy Layer

Authorization decisions are evaluated in two explicit stages:

1. Static RBAC grant + scope evaluation in `app/features/auth/service.py`.
1. Optional conditional policy evaluation in `app/core/authorization/dependencies.py`.

Conditional deny responses return `403 forbidden` with:

- `meta.permission_id`
- `meta.authorization_stage = "conditional_policy"`

## Read Endpoint Access Policy

Canonical read-access definitions live in `READ_ACCESS_POLICY_CATALOG` in
`app/core/authorization/catalog.py`.
This table is contract-checked by `tests/routers/test_authorization_policy_coverage.py`.

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

## Base Role Catalog (Bootstrap)

Seed source: `utils/rbac_bootstrap.py`

| Role          | Base Permissions                                                               |
| ------------- | ------------------------------------------------------------------------------ |
| `admin_role`  | `roles:manage`, `role_permissions:manage`, `user_roles:manage`, `users:manage` |
| `reader_role` | none                                                                           |

## Notes

- Missing permission returns `403 forbidden` with `meta.permission_id`.
- Bootstrap command is idempotent: `python -m utils.rbac_bootstrap`.
