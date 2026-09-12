# Frontend API Consumer and Error Contract Matrix

This document is the canonical consumer-side inventory of backend endpoints used by the frontend.

## Endpoint Consumer Catalog

| Endpoint                                            | Method   | Consumer Module             | Consumer Function           | Auth Mode | Success Contract                              |
| --------------------------------------------------- | -------- | --------------------------- | --------------------------- | --------- | --------------------------------------------- |
| `/token`                                            | `POST`   | `shared/auth/session.ts`    | `loginWithCredentials`      | `public`  | `access_token` + `token_type`                 |
| `/users/register`                                   | `POST`   | `shared/auth/session.ts`    | `registerUser`              | `public`  | authenticated user + `permissions[]` snapshot |
| `/users/me`                                         | `GET`    | `shared/auth/session.ts`    | `readCurrentUser`           | `bearer`  | authenticated user + `permissions[]` snapshot |
| `/users/me`                                         | `PATCH`  | `shared/auth/session.ts`    | `updateCurrentUser`         | `bearer`  | authenticated user + `permissions[]` snapshot |
| `/audit-log`                                        | `GET`    | `features/audit-log/api.ts` | `readAuditLogEntries`       | `bearer`  | `AuditLogEntry[]`                             |
| `/rbac/users`                                       | `GET`    | `shared/rbac/admin.ts`      | `readAdminUsers`            | `bearer`  | `AdminUser[]`                                 |
| `/rbac/users`                                       | `POST`   | `shared/rbac/admin.ts`      | `createAdminUser`           | `bearer`  | `AdminUser`                                   |
| `/rbac/users/{user_id}`                             | `GET`    | `shared/rbac/admin.ts`      | `readAdminUser`             | `bearer`  | `AdminUser`                                   |
| `/rbac/users/{user_id}/roles`                       | `GET`    | `shared/rbac/admin.ts`      | `readRbacUserRoles`         | `bearer`  | `AssignedRole[]`                              |
| `/rbac/users/{user_id}`                             | `PUT`    | `shared/rbac/admin.ts`      | `updateAdminUser`           | `bearer`  | `AdminUser`                                   |
| `/rbac/users/{user_id}`                             | `DELETE` | `shared/rbac/admin.ts`      | `softDeleteAdminUser`       | `bearer`  | `204 no-content`                              |
| `/rbac/roles`                                       | `GET`    | `shared/rbac/admin.ts`      | `readRbacRoles`             | `bearer`  | `RbacRole[]`                                  |
| `/rbac/roles`                                       | `POST`   | `shared/rbac/admin.ts`      | `createRbacRole`            | `bearer`  | `RbacRole`                                    |
| `/rbac/roles/{role_id}/users`                       | `GET`    | `shared/rbac/admin.ts`      | `readRbacRoleUsers`         | `bearer`  | `AssignedUser[]`                              |
| `/rbac/roles/{role_id}`                             | `PUT`    | `shared/rbac/admin.ts`      | `updateRbacRole`            | `bearer`  | `RbacRole`                                    |
| `/rbac/roles/{role_id}`                             | `DELETE` | `shared/rbac/admin.ts`      | `deleteRbacRole`            | `bearer`  | `204 no-content`                              |
| `/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `PUT`    | `shared/rbac/admin.ts`      | `assignRbacRoleInheritance` | `bearer`  | `204 no-content`                              |
| `/rbac/roles/{role_id}/inherits/{parent_role_id}`   | `DELETE` | `shared/rbac/admin.ts`      | `removeRbacRoleInheritance` | `bearer`  | `204 no-content`                              |
| `/rbac/permissions`                                 | `GET`    | `shared/rbac/admin.ts`      | `readRbacPermissions`       | `bearer`  | `RbacPermission[]`                            |
| `/rbac/roles/{role_id}/permissions/{permission_id}` | `PUT`    | `shared/rbac/admin.ts`      | `assignRbacRolePermission`  | `bearer`  | `RbacRolePermission`                          |
| `/rbac/roles/{role_id}/permissions/{permission_id}` | `DELETE` | `shared/rbac/admin.ts`      | `removeRbacRolePermission`  | `bearer`  | `204 no-content`                              |
| `/rbac/users/{user_id}/roles/{role_id}`             | `PUT`    | `shared/rbac/admin.ts`      | `assignRbacUserRole`        | `bearer`  | `UserRoleAssignmentResponse`                  |
| `/rbac/users/{user_id}/roles/{role_id}`             | `DELETE` | `shared/rbac/admin.ts`      | `removeRbacUserRole`        | `bearer`  | `204 no-content`                              |

## Conditional Consumer Notes

- `readAuditLogEntries` is routed through `/admin/audit-log`, which requires `audit_logs:read` before the page can request the endpoint.
- `readRbacRoles` is permission-gated on `/admin/users`: the page only requests `/rbac/roles` when the current session has `roles:manage`; otherwise it hides role-related controls and does not send `role_ids`.

## Error Contract Matrix

| Endpoint            | Expected Error Codes                                                                                                   | Request-ID Policy                                      | Frontend Handling Contract                                                                                                     |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `/token`            | `invalid_input`, `unauthorized`, `forbidden`, `rate_limited`, `service_unavailable`, `internal_error`, `network_error` | Use `X-Request-ID`/payload `request_id` when available | Show user-safe login error and append request-id diagnostic for support; do not treat limiter outage as bad credentials.       |
| `/users/register`   | `invalid_input`, `conflict`, `rate_limited`, `service_unavailable`, `internal_error`, `network_error`                  | Use `X-Request-ID`/payload `request_id` when available | Keep auth/session unchanged; honor quota feedback and expose request-id diagnostics without automatic retry.                   |
| `/users/me`         | `invalid_input`, `unauthorized`, `forbidden`, `conflict`, `internal_error`, `network_error`                            | Use `X-Request-ID`/payload `request_id` when available | `GET` unauthorized clears session; successful `PATCH` writes through `SESSION_QUERY_KEY`; unauthorized `PATCH` clears session. |
| `/audit-log`        | `unauthorized`, `forbidden`, `network_error`, `internal_error`                                                         | Use `X-Request-ID`/payload `request_id` when available | Show audit log error panel with backend detail and request-id diagnostic.                                                      |
| `/rbac/users*`      | `invalid_input`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `network_error`, `internal_error`               | Use `X-Request-ID`/payload `request_id` when available | Show admin error panel with backend detail and request-id diagnostic.                                                          |
| `/rbac/roles*`      | `invalid_input`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `network_error`, `internal_error`               | Use `X-Request-ID`/payload `request_id` when available | Keep page interactive; explicit-scope permission mutations surface diagnostics without silent fallback.                        |
| `/rbac/permissions` | `unauthorized`, `forbidden`, `network_error`, `internal_error`                                                         | Use `X-Request-ID`/payload `request_id` when available | Permission catalog failures block role-permission actions and show diagnostics.                                                |

## Error Normalization and Diagnostic Paths

1. Every JSON consumer supplies an explicit runtime parser to `apiRequest`; TypeScript rejects a
   JSON request without one. The shared client never casts an unvalidated payload to `T`.
1. Every catalog entry marked `204 no-content` uses `apiNoContentRequest`. That path accepts only
   status `204` and never attempts JSON parsing; the JSON path rejects an unexpected `204`.
1. Invalid JSON, a parser failure, an unexpected JSON-path `204`, or unexpected content on the
   no-content path becomes `ApiError` code `invalid_response`, keeps the actual HTTP status, uses
   the safe message `Respuesta invalida del servidor`, and preserves a non-empty response
   `X-Request-ID`. Parser and payload details are never emitted.
1. An error response body is untrusted JSON. Only non-empty string values for `detail`, `code`, and
   `request_id` are accepted; invalid JSON, arrays, and incorrectly typed properties fall back to a
   safe status or communication message.
1. A non-empty response `X-Request-ID` header takes precedence over payload `request_id`; the
   payload value is used only when that header is absent or empty.
1. The endpoint templates in the catalog are the caller-owned `diagnosticPath` values for dynamic
   RBAC requests. Static endpoint paths remain unchanged.
1. The shared HTTP client removes query strings and fragments from every diagnostic path. It does
   not infer identifier normalization and never emits request bodies, tokens, or search terms.
1. Runtime correlation follows a bounded, cycle-safe `Error.cause` chain so wrapped API failures
   retain `request_id` and `is_api_error` classification.
1. `rate_limited` means the quota was exhausted and may include numeric retry/quota headers;
   `service_unavailable` means the required backend limiter store failed closed. The generic parser
   preserves either code and `request_id`; callers must not automatically retry mutations.

## Drift Control Rules

1. Endpoint additions/removals in frontend API consumers must update this matrix in the same PR.
1. Contract parser changes in `shared/api/contracts.ts`, `shared/auth/contracts.ts`, or `shared/rbac/contracts.ts` must reflect here when payload expectations change.
1. Error normalization behavior updates in `shared/api/errors.ts` must keep this matrix synchronized.
1. Role-permission assignment UI must send an explicit scope (`own`, `tenant`, or `any`) and must not rely on a client-side default.
1. Every dynamic API consumer must pass the matching catalog template as `diagnosticPath`; adding a
   normalization rule requires a verifiable route contract and tests.
1. Blob and binary response support is outside the shared JSON/no-content client contract until a
   real consumer and separate validation rules are accepted.
