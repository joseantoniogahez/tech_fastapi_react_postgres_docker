# Frontend Mutation Policy Matrix

This document defines deterministic mutation retry and invalidation behavior by domain.

## Policy Matrix

| Domain               | Retry Policy                 | Invalidation Strategy                                  |
| -------------------- | ---------------------------- | ------------------------------------------------------ |
| Default mutation     | No inherited automatic retry | Caller-defined                                         |
| Auth login mutation  | No retry                     | Set `SESSION_QUERY_KEY` and invalidate session query   |
| Auth logout mutation | No retry                     | Clear `SESSION_QUERY_KEY` and invalidate session query |

## Implementation References

- Mutation policies: `src/app/mutation-policy.ts`
- QueryClient defaults: `src/app/query-client.ts`
- Login mutation consumer: `src/features/auth/LoginPage.tsx`
- Logout mutation consumer: `src/shared/routing/RootLayout.tsx`

## Failure Behavior Contract

- Registration, profile/password updates, RBAC changes, deletes, login, and logout never inherit
  an automatic retry.
- A caller may opt in only when the backend contract proves the operation is idempotent, including
  any required idempotency key and replay semantics. The caller must name that contract and test
  duplicate-delivery behavior in the same change. There is no current opt-in consumer.
- A failed mutation remains available for deliberate user resubmission through its existing form
  or action state; this is not an automatic retry.
- Query retries are independent and remain limited to one retry for transient/network failures as
  defined in `src/app/query-policy.ts`.
