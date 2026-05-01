# Frontend Support Diagnostics Runbook

This runbook defines triage flow and error-code diagnostics for frontend incidents.

## Triage Flow

1. Capture user-visible error message and timestamp.
1. Capture `request_id` when present in UI diagnostics.
1. Correlate with frontend observability events (`event_name`, `request_id`, route, endpoint path).
1. Classify issue by error taxonomy and apply first response action.
1. Escalate with artifact bundle (request id, route, endpoint, error code, reproduction steps).

## Error Taxonomy and Actions

| Error Code       | Typical Surface                    | Initial Action                                                     | Escalation Trigger                                     |
| ---------------- | ---------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------ |
| `unauthorized`   | Login/protected route              | Verify token/session state and expected auth flow.                 | Repeated auth failures for valid accounts.             |
| `forbidden`      | Protected API operation            | Verify permission scope and user role mapping.                     | Policy mismatch between backend authz and UI behavior. |
| `internal_error` | API request or route fallback      | Use `request_id` for backend correlation; gather impacted endpoint | Any persistent 5xx pattern.                            |
| `network_error`  | API communication failure          | Validate connectivity/API origin/runtime config.                   | Widespread outage across users/regions.                |
| `invalid_input`  | Form submission / API parsing path | Validate payload contract expectations and user input constraints. | Contract drift or backend schema mismatch.             |

## Required Incident Artifact

- Frontend route path
- Endpoint path (if API-related)
- Error code
- `request_id` (if available)
- User-visible message text
- Browser/runtime context

## References

- Event schema: `docs/operations/observability_events.md`
- Runtime pipeline: `docs/operations/runtime_error_pipeline.md`
- API consumer matrix: `docs/operations/api_consumer_matrix.md`
