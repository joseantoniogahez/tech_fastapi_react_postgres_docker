# Frontend Global Runtime Error Pipeline

This document defines the global capture behavior for uncaught runtime errors and unhandled promise rejections.

## Scope

- `window.error` events
- `window.unhandledrejection` events

## Behavior Contract

- Handlers are installed once at app bootstrap (`src/main.tsx`).
- Captured failures emit structured observability events through `src/shared/observability/events.ts`.
- Correlation behavior:
  - If a runtime failure is or wraps an `ApiError`, `request_id` is propagated and `is_api_error`
    is `true` for unhandled rejections.
  - Otherwise, `request_id` is logged as `null`.
- `Error.cause` traversal accepts direct, wrapped, and nested errors, has a maximum depth of `8`,
  and stops on repeated objects to prevent cycles.
- The first `ApiError` in the bounded cause chain with a non-empty request ID supplies correlation.
  An `ApiError` without correlation still makes `is_api_error` true.
- The emitted reason remains the outer error message. Causes, stacks, request bodies, and raw URLs
  are not serialized into the event.

## Implementation and Tests

- Implementation: `src/shared/observability/runtime-errors.ts`
- Tests: `src/shared/observability/runtime-errors.test.ts`
