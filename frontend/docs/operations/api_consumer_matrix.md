# Frontend API Consumer and Error Contract Matrix

This document is the canonical consumer-side inventory of backend endpoints used by the frontend.

## Endpoint Consumer Catalog

| Endpoint    | Method | Consumer Module          | Consumer Function      | Auth Mode | Success Contract              |
| ----------- | ------ | ------------------------ | ---------------------- | --------- | ----------------------------- |
| `/token`    | `POST` | `shared/auth/session.ts` | `loginWithCredentials` | `public`  | `access_token` + `token_type` |
| `/users/me` | `GET`  | `shared/auth/session.ts` | `readCurrentUser`      | `bearer`  | authenticated user payload    |

## Error Contract Matrix

| Endpoint    | Expected Error Codes                                                  | Request-ID Policy                                      | Frontend Handling Contract                                               |
| ----------- | --------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------ |
| `/token`    | `unauthorized`, `validation_error`, `internal_error`, `network_error` | Use `X-Request-ID`/payload `request_id` when available | Show user-safe login error and append request-id diagnostic for support. |
| `/users/me` | `unauthorized`, `forbidden`, `internal_error`, `network_error`        | Use `X-Request-ID`/payload `request_id` when available | Unauthorized clears session; other failures surface diagnostic state.    |

## Drift Control Rules

1. Endpoint additions/removals in frontend API consumers must update this matrix in the same PR.
1. Contract parser changes in `shared/api/contracts.ts` or `shared/auth/contracts.ts` must reflect here when payload expectations change.
1. Error normalization behavior updates in `shared/api/errors.ts` must keep this matrix synchronized.
