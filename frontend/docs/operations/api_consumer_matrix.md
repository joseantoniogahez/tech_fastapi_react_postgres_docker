# Frontend API Consumer and Error Contract Matrix

This document is the canonical consumer-side inventory of backend endpoints used by the frontend.

## Endpoint Consumer Catalog

| Endpoint                                            | Method   | Consumer Module          | Consumer Function           | Auth Mode | Success Contract              |
| --------------------------------------------------- | -------- | ------------------------ | --------------------------- | --------- | ----------------------------- |
| `/token`                                            | `POST`   | `shared/auth/session.ts` | `loginWithCredentials`      | `public`  | `access_token` + `token_type` |
| `/users/me`                                         | `GET`    | `shared/auth/session.ts` | `readCurrentUser`           | `bearer`  | authenticated user payload    |
| `/rbac/users`                                       | `GET`    | `shared/rbac/admin.ts`   | `readAdminUsers`            | `bearer`  | `AdminUser[]`                 |
| `/rbac/users/{user_id}`                             | `GET`    | `shared/rbac/admin.ts`   | `readAdminUser`             | `bearer`  | `AdminUser`                   |
| `/rbac/users`                                       | `POST`   | `shared/rbac/admin.ts`   | `createAdminUser`           | `bearer`  | `AdminUser`                   |
| `/rbac/users/{user_id}`                             | `PUT`    | `shared/rbac/admin.ts`   | `updateAdminUser`           | `bearer`  | `AdminUser`                   |
| `/rbac/users/{user_id}`                             | `DELETE` | `shared/rbac/admin.ts`   | `softDeleteAdminUser`       | `bearer`  | `204 no-content`              |
| `/rbac/roles`                                       | `GET`    | `shared/rbac/admin.ts`   | `readRbacRoles`             | `bearer`  | `RbacRole[]`                  |
| `/rbac/roles`                                       | `POST`   | `shared/rbac/admin.ts`   | `createRbacRole`            | `bearer`  | `RbacRole`                    |
| `/rbac/roles/{role_id}`                             | `PUT`    | `shared/rbac/admin.ts`   | `updateRbacRole`            | `bearer`  | `RbacRole`                    |
| `/rbac/roles/{role_id}`                             | `DELETE` | `shared/rbac/admin.ts`   | `deleteRbacRole`            | `bearer`  | `204 no-content`              |
| `/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `PUT`    | `shared/rbac/admin.ts`   | `assignRbacRoleInheritance` | `bearer`  | `204 no-content`              |
| `/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `DELETE` | `shared/rbac/admin.ts`   | `removeRbacRoleInheritance` | `bearer`  | `204 no-content`              |
| `/rbac/permissions`                                 | `GET`    | `shared/rbac/admin.ts`   | `readRbacPermissions`       | `bearer`  | `RbacPermission[]`            |
| `/rbac/roles/{role_id}/permissions/{permission_id}` | `PUT`    | `shared/rbac/admin.ts`   | `assignRbacRolePermission`  | `bearer`  | `RbacRolePermission`          |
| `/rbac/roles/{role_id}/permissions/{permission_id}` | `DELETE` | `shared/rbac/admin.ts`   | `removeRbacRolePermission`  | `bearer`  | `204 no-content`              |

## Error Contract Matrix

| Endpoint            | Expected Error Codes                                                                                     | Request-ID Policy                                      | Frontend Handling Contract                                                       |
| ------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------- |
| `/token`            | `unauthorized`, `validation_error`, `internal_error`, `network_error`                                    | Use `X-Request-ID`/payload `request_id` when available | Show user-safe login error and append request-id diagnostic for support.         |
| `/users/me`         | `unauthorized`, `forbidden`, `internal_error`, `network_error`                                           | Use `X-Request-ID`/payload `request_id` when available | Unauthorized clears session; other failures surface diagnostic state.            |
| `/rbac/users*`      | `invalid_input`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `network_error`, `internal_error` | Use `X-Request-ID`/payload `request_id` when available | Show admin error panel with backend detail and request-id diagnostic.            |
| `/rbac/roles*`      | `invalid_input`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `network_error`, `internal_error` | Use `X-Request-ID`/payload `request_id` when available | Keep page interactive; mutation/list errors are surfaced without silent retries. |
| `/rbac/permissions` | `unauthorized`, `forbidden`, `network_error`, `internal_error`                                           | Use `X-Request-ID`/payload `request_id` when available | Permission catalog failures block role-permission actions and show diagnostics.  |

## Drift Control Rules

1. Endpoint additions/removals in frontend API consumers must update this matrix in the same PR.
1. Contract parser changes in `shared/api/contracts.ts`, `shared/auth/contracts.ts`, or `shared/rbac/contracts.ts` must reflect here when payload expectations change.
1. Error normalization behavior updates in `shared/api/errors.ts` must keep this matrix synchronized.
