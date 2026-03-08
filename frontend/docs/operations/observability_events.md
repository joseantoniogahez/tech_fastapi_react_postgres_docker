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

- Sensitive keys are redacted before logging:
  - `authorization`
  - `password`
  - `token`
  - `access_token`

## Core Event Names

- `api.request.network_error`
- `api.request.response_error`
- `routing.protected.error`
- `routing.route_error`
- `runtime.error`
- `runtime.unhandled_rejection`

## References

- Event emitter: `src/shared/observability/events.ts`
- Event tests: `src/shared/observability/events.test.ts`
