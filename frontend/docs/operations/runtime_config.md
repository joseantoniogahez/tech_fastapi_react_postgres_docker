# Frontend Runtime Configuration Contract

This document defines the runtime configuration contract enforced by frontend startup and API utilities.

## Required Configuration

| Variable             | Purpose            | Validation Rule                         | Default                 |
| -------------------- | ------------------ | --------------------------------------- | ----------------------- |
| `VITE_API_ORIGIN`    | Backend API origin | Must be a valid `http` or `https` URL   | `http://localhost:8000` |
| `VITE_API_BASE_PATH` | API prefix path    | Must be non-empty and contain no spaces | `/v1`                   |

## Fail-Fast Behavior

- Frontend startup calls `readFrontendEnvConfig()` from `src/shared/api/env.ts`.
- Invalid configuration throws `FrontendEnvError` and blocks runtime boot.
- API URL builders (`getApiBaseUrl`, `buildApiUrl`) use the same validated config path.

## Validation References

- Contract tests: `src/shared/api/env.test.ts`
- Runtime bootstrap: `src/main.tsx`
