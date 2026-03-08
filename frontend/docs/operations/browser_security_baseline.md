# Frontend Browser Security Baseline

This document defines the minimum browser-security policy contract required for frontend delivery.

## Required Baseline Policies

| Policy                        | Mechanism in Frontend Artifact                               | Required Value/Intent                                                                                   |
| ----------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| Content Security Policy (CSP) | `meta[http-equiv="Content-Security-Policy"]` in `index.html` | Restrict sources to self + explicit browser-safe allowances; deny framing via `frame-ancestors 'none'`. |
| Referrer Policy               | `meta[name="referrer"]` in `index.html`                      | `strict-origin-when-cross-origin`                                                                       |
| Permissions Policy            | `meta[http-equiv="Permissions-Policy"]` in `index.html`      | Disable geolocation, microphone, and camera by default.                                                 |

## Ownership and Enforcement

- Frontend owns policy artifact presence and contract tests.
- Deployment owners must align server headers with or stronger than this baseline.
- Route/script-loading changes must not remove or weaken this baseline without explicit review.

## Validation References

- Contract tests: `src/contracts/browser-security.contract.test.ts`
- Artifact under contract: `frontend/index.html`
