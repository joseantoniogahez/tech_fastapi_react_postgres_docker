# Frontend Runtime Configuration Contract

This document defines the Vite build-time configuration contract enforced when the browser starts
and by the shared API utilities. These values are embedded in the static bundle at build time; they
are not read from the static container environment when that container starts.

## Required Configuration

| Variable             | Purpose            | Validation Rule                                                                                                                                       | Default                 |
| -------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| `VITE_API_ORIGIN`    | Backend API origin | Must be an HTTP(S) URL normalized to the canonical `URL.origin`; it must not contain user information, a non-root path, a query string, or a fragment | `http://localhost:8000` |
| `VITE_API_BASE_PATH` | API prefix path    | Must be a non-empty string without spaces; it is validated independently, normalized to a leading-slash path, and `/` collapses to an empty base path | `/v1`                   |

`URL.origin` canonicalization lowercases the host, removes a default protocol port, preserves a
non-default port, and omits the trailing root slash. API path configuration belongs only in
`VITE_API_BASE_PATH`.

## Fail-Fast Behavior

- Vite resolves `VITE_*` values while building the bundle.
- Browser startup calls `readFrontendEnvConfig()` from `src/shared/api/env.ts`.
- Invalid embedded configuration throws `FrontendEnvError` and blocks browser boot before requests.
- API URL builders (`getApiBaseUrl`, `buildApiUrl`) use the same validated config path.
- Changing either value after an artifact exists requires a new build and deployment.

## Validation References

- Contract tests: `src/shared/api/env.test.ts`
- Runtime bootstrap: `src/main.tsx`
