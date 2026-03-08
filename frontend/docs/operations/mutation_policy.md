# Frontend Mutation Policy Matrix

This document defines deterministic mutation retry and invalidation behavior by domain.

## Policy Matrix

| Domain               | Retry Policy                                     | Invalidation Strategy                                  |
| -------------------- | ------------------------------------------------ | ------------------------------------------------------ |
| Default mutation     | Retry only transient/network errors, max 1 retry | Caller-defined                                         |
| Auth login mutation  | No retry                                         | Set `SESSION_QUERY_KEY` and invalidate session query   |
| Auth logout mutation | No retry                                         | Clear `SESSION_QUERY_KEY` and invalidate session query |

## Implementation References

- Mutation policies: `src/app/mutation-policy.ts`
- QueryClient defaults: `src/app/query-client.ts`
- Login mutation consumer: `src/features/auth/LoginPage.tsx`
- Logout mutation consumer: `src/features/welcome/WelcomePage.tsx`

## Failure Behavior Contract

- `401` and `409` mutation failures are non-retryable.
- Transient/network failures retry once under default mutation policy.
- Auth mutations never retry to avoid duplicate auth-side effects and confusing user state.
