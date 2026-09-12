# Frontend Browser Security Baseline

This document defines the browser-security policy enforced by the production static server.

## Required Response Headers

Every successful SPA document response, including a client-route fallback, must send:

| Header                    | Required value or policy                                                                                                                     |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `Content-Security-Policy` | Restrictive same-origin defaults, the configured API origin in `connect-src`, asset sources used by the bundle, and `frame-ancestors 'none'` |
| `Permissions-Policy`      | `geolocation=(), microphone=(), camera=()`                                                                                                   |
| `Referrer-Policy`         | `strict-origin-when-cross-origin`                                                                                                            |
| `X-Content-Type-Options`  | `nosniff`                                                                                                                                    |
| `X-Frame-Options`         | `DENY`                                                                                                                                       |

The current CSP is:

```text
default-src 'self'; base-uri 'self'; connect-src 'self' <validated-api-origin>; font-src 'self' data: https://fonts.gstatic.com; form-action 'self'; frame-ancestors 'none'; frame-src 'none'; img-src 'self' data:; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com
```

`connect-src` must contain only `'self'` and the canonical build-time `VITE_API_ORIGIN`. It must not
contain `*`, `http:`, or `https:` as open source expressions. `VITE_API_BASE_PATH` is intentionally
absent because CSP authorizes origins rather than application paths.

## Build-Time Generation

`scripts/generate-serve-config.mjs` validates `VITE_API_ORIGIN` as an HTTP(S) `URL.origin`,
canonicalizes it, and writes a deterministic `.generated/serve.json`. The production image copies
that artifact outside the public directory and starts pinned `serve` with `-s` for the SPA fallback
and `-c /app/serve.json` for response headers.

The configuration is coupled to the same build arguments as the Vite bundle. Changing the API
origin requires rebuilding the image; the static container has no Vite runtime environment.

## Markup Scope

`index.html` retains the compatible referrer meta element as a development defense. CSP framing
protection, Permissions Policy, MIME protection, and compatibility framing protection are HTTP
response-header concerns. The markup does not claim to enforce directives unsupported in meta
elements, and the response header is authoritative in production.

## Validation

Automated header smoke validates response policy, but it does not replace manual browser inspection
for extension behavior, mixed-content warnings, or deployment-edge header rewriting.

- `src/contracts/browser-security.contract.test.ts` verifies generation, unsafe-origin rejection,
  Docker coupling, and the markup/documentation boundary.
- `npm run test:security-headers` exercises the checker against real HTTP responses and verifies it
  fails closed for an open `connect-src`.
- `scripts/security-headers-smoke.mjs <frontend-origin> <expected-api-origin>` requests both `/` and
  an unknown client route, then inspects their actual headers and SPA bodies.
- CI builds the production image and runs that smoke against the container. A local image gate needs
  a running Docker Engine.

## Ownership and Change Rules

- Frontend owns the generated `serve` configuration, response contract, checker, and tests.
- Platform owners must preserve these headers or provide stronger values at an upstream proxy.
- Route, asset, API-origin, font, or static-server changes require a CSP and real-response review.
- A server change requires a separate architecture decision and equivalent root/fallback smoke.
