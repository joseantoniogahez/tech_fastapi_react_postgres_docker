# Frontend Observability Event Contract

This document defines the standardized frontend observability schema for API, routing, and runtime diagnostics.

## Event Schema

Required fields:

- `event_name`: stable event identifier.
- `level`: `info` | `warn` | `error`.
- `timestamp`: ISO-8601 timestamp emitted at event time.
- `request_id`: backend correlation id when available; otherwise `null`.
- `context`: redaction-safe metadata map.

## Redaction Rules

- Sensitive keys are redacted recursively before logging while preserving the surrounding object
  and array structure:
  - `access_token`
  - `authorization`
  - `password`
  - `refresh_token`
  - `token`
- Sanitization does not mutate the source context.
- API event context never includes request bodies, request headers, tokens, or search terms.

## Diagnostic API Paths

- `toDiagnosticApiPath` removes the complete query string and fragment before an API path enters an
  event. Static paths such as `/users/me` remain available for diagnosis.
- A dynamic API consumer supplies a caller-owned static `diagnosticPath` matching the canonical
  endpoint template, for example `/rbac/users/{user_id}`. The actual request URL still reaches
  `fetch`, but identifiers and encoded values do not enter diagnostics.
- Identifiers may be normalized only when a verifiable route rule exists. The shared HTTP client
  does not infer templates by rewriting user-controlled values.
- Supplying a `diagnosticPath` does not permit query strings or fragments; the same removal helper
  is applied to it before emission.

## Correlation

- For API response errors, a non-empty response `X-Request-ID` header takes precedence over a
  string `request_id` in the JSON payload.
- Runtime handlers preserve correlation through bounded `Error.cause` chains as defined in the
  runtime error pipeline.

## Core Event Names

- `api.request.network_error`
- `api.request.response_error`
- `routing.protected.error`
- `routing.route_error`
- `runtime.error`
- `runtime.unhandled_rejection`

`api.request.response_error` also represents the client-side `invalid_response` contract for
invalid JSON, runtime parser failure, and JSON/no-content status mismatches. Its context contains
only method, static diagnostic path, actual status, and code; `request_id` comes from the response
header when available, and parser exceptions or response payloads are not emitted.

## References

- Event emitter: `src/shared/observability/events.ts`
- Event tests: `src/shared/observability/events.test.ts`
