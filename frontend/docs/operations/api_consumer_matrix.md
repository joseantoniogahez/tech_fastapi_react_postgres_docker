# Frontend API Consumer and Error Contract Matrix

This document is the canonical consumer-side inventory of backend endpoints used by the frontend.

## Endpoint Consumer Catalog

| Endpoint                                            | Method   | Consumer Module          | Consumer Function           | Auth Mode | Success Contract                              |
| --------------------------------------------------- | -------- | ------------------------ | --------------------------- | --------- | --------------------------------------------- |
| `/token`                                            | `POST`   | `shared/auth/session.ts` | `loginWithCredentials`      | `public`  | `access_token` + `token_type`                 |
| `/users/register`                                   | `POST`   | `shared/auth/session.ts` | `registerUser`              | `public`  | authenticated user + `permissions[]` snapshot |
| `/users/me`                                         | `GET`    | `shared/auth/session.ts` | `readCurrentUser`           | `bearer`  | authenticated user + `permissions[]` snapshot |
| `/users/me`                                         | `PATCH`  | `shared/auth/session.ts` | `updateCurrentUser`         | `bearer`  | authenticated user + `permissions[]` snapshot |
| `/rbac/users`                                       | `GET`    | `shared/rbac/admin.ts`   | `readAdminUsers`            | `bearer`  | `AdminUser[]`                                 |
| `/rbac/users`                                       | `POST`   | `shared/rbac/admin.ts`   | `createAdminUser`           | `bearer`  | `AdminUser`                                   |
| `/rbac/users/{user_id}`                             | `GET`    | `shared/rbac/admin.ts`   | `readAdminUser`             | `bearer`  | `AdminUser`                                   |
| `/rbac/users/{user_id}/roles`                       | `GET`    | `shared/rbac/admin.ts`   | `readRbacUserRoles`         | `bearer`  | `AssignedRole[]`                              |
| `/rbac/users/{user_id}`                             | `PUT`    | `shared/rbac/admin.ts`   | `updateAdminUser`           | `bearer`  | `AdminUser`                                   |
| `/rbac/users/{user_id}`                             | `DELETE` | `shared/rbac/admin.ts`   | `softDeleteAdminUser`       | `bearer`  | `204 no-content`                              |
| `/rbac/roles`                                       | `GET`    | `shared/rbac/admin.ts`   | `readRbacRoles`             | `bearer`  | `RbacRole[]`                                  |
| `/rbac/roles`                                       | `POST`   | `shared/rbac/admin.ts`   | `createRbacRole`            | `bearer`  | `RbacRole`                                    |
| `/rbac/roles/{role_id}/users`                       | `GET`    | `shared/rbac/admin.ts`   | `readRbacRoleUsers`         | `bearer`  | `AssignedUser[]`                              |
| `/rbac/roles/{role_id}`                             | `PUT`    | `shared/rbac/admin.ts`   | `updateRbacRole`            | `bearer`  | `RbacRole`                                    |
| `/rbac/roles/{role_id}`                             | `DELETE` | `shared/rbac/admin.ts`   | `deleteRbacRole`            | `bearer`  | `204 no-content`                              |
| `/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `PUT`    | `shared/rbac/admin.ts`   | `assignRbacRoleInheritance` | `bearer`  | `204 no-content`                              |
| `/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `DELETE` | `shared/rbac/admin.ts`   | `removeRbacRoleInheritance` | `bearer`  | `204 no-content`                              |
| `/rbac/permissions`                                 | `GET`    | `shared/rbac/admin.ts`   | `readRbacPermissions`       | `bearer`  | `RbacPermission[]`                            |
| `/rbac/roles/{role_id}/permissions/{permission_id}` | `PUT`    | `shared/rbac/admin.ts`   | `assignRbacRolePermission`  | `bearer`  | `RbacRolePermission`                          |
| `/rbac/roles/{role_id}/permissions/{permission_id}` | `DELETE` | `shared/rbac/admin.ts`   | `removeRbacRolePermission`  | `bearer`  | `204 no-content`                              |
| `/rbac/users/{user_id}/roles/{role_id}`             | `PUT`    | `shared/rbac/admin.ts`   | `assignRbacUserRole`        | `bearer`  | `UserRoleAssignmentResponse`                  |
| `/rbac/users/{user_id}/roles/{role_id}`             | `DELETE` | `shared/rbac/admin.ts`   | `removeRbacUserRole`        | `bearer`  | `204 no-content`                              |

## Error Contract Matrix

| Endpoint            | Expected Error Codes                                                                                     | Request-ID Policy                                      | Frontend Handling Contract                                                                                                     |
| ------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `/token`            | `unauthorized`, `validation_error`, `internal_error`, `network_error`                                    | Use `X-Request-ID`/payload `request_id` when available | Show user-safe login error and append request-id diagnostic for support.                                                       |
| `/users/register`   | `invalid_input`, `conflict`, `internal_error`, `network_error`                                           | Use `X-Request-ID`/payload `request_id` when available | Show deterministic registration feedback, keep auth/session state unchanged, and expose diagnostics when available.            |
| `/users/me`         | `invalid_input`, `unauthorized`, `forbidden`, `conflict`, `internal_error`, `network_error`              | Use `X-Request-ID`/payload `request_id` when available | `GET` unauthorized clears session; successful `PATCH` writes through `SESSION_QUERY_KEY`; unauthorized `PATCH` clears session. |
| `/rbac/users*`      | `invalid_input`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `network_error`, `internal_error` | Use `X-Request-ID`/payload `request_id` when available | Show admin error panel with backend detail and request-id diagnostic.                                                          |
| `/rbac/roles*`      | `invalid_input`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `network_error`, `internal_error` | Use `X-Request-ID`/payload `request_id` when available | Keep page interactive; explicit-scope permission mutations surface diagnostics without silent fallback.                        |
| `/rbac/permissions` | `unauthorized`, `forbidden`, `network_error`, `internal_error`                                           | Use `X-Request-ID`/payload `request_id` when available | Permission catalog failures block role-permission actions and show diagnostics.                                                |

## Drift Control Rules

1. Endpoint additions/removals in frontend API consumers must update this matrix in the same PR.
1. Contract parser changes in `shared/api/contracts.ts`, `shared/auth/contracts.ts`, or `shared/rbac/contracts.ts` must reflect here when payload expectations change.
1. Error normalization behavior updates in `shared/api/errors.ts` must keep this matrix synchronized.
1. Role-permission assignment UI must send an explicit scope (`own`, `tenant`, or `any`) and must not rely on a client-side default.
