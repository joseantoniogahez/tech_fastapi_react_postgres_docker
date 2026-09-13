# Frontend Support Diagnostics Runbook

This runbook defines triage flow and error-code diagnostics for frontend incidents.

## Triage Flow

1. Capture user-visible error message and timestamp.
1. Capture `request_id` when present in UI diagnostics.
1. Correlate with frontend observability events (`event_name`, `request_id`, route, static endpoint
   template).
1. Classify issue by error taxonomy and apply first response action.
1. Escalate with artifact bundle (request id, route, static endpoint template, error code,
   reproduction steps).

## Privacy Boundary

- Do not capture raw request URLs. API diagnostics remove query strings and fragments before
  emission.
- For dynamic endpoints, record the canonical static template such as
  `/rbac/users/{user_id}` rather than an identifier-bearing path.
- Do not collect request bodies, authorization values, tokens, passwords, names, phone numbers,
  search terms, or other personal data in an incident artifact.
- A `request_id` is the supported per-request correlation value. It is not a substitute for copying
  sensitive request data.

## Error Taxonomy and Actions

| Error Code            | Typical Surface                     | Initial Action                                                        | Escalation Trigger                                     |
| --------------------- | ----------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------ |
| `unauthorized`        | Login/protected route               | Verify token/session state and expected auth flow.                    | Repeated auth failures for valid accounts.             |
| `forbidden`           | Protected API operation             | Verify permission scope and user role mapping.                        | Policy mismatch between backend authz and UI behavior. |
| `internal_error`      | API request or route fallback       | Use `request_id` for backend correlation; gather impacted endpoint    | Any persistent 5xx pattern.                            |
| `network_error`       | API communication failure           | Validate connectivity/API origin/runtime config.                      | Widespread outage across users/regions.                |
| `invalid_input`       | Form submission / API parsing path  | Validate payload contract expectations and user input constraints.    | Contract drift or backend schema mismatch.             |
| `not_found`           | Route or requested API resource     | Verify the route/resource identifier and refresh stale UI state.      | Repeated misses for resources known to exist.          |
| `conflict`            | Create or update operation          | Refresh current state and resolve the reported version/name conflict. | Repeated conflicts after state refresh.                |
| `invalid_response`    | Successful HTTP response validation | Correlate by request id and compare endpoint status/schema contract.  | Any reproducible parser or JSON/no-content mismatch.   |
| `rate_limited`        | Login or registration               | Honor `Retry-After`; avoid repeated manual or automatic submission.   | Sustained quota exhaustion across unrelated clients.   |
| `service_unavailable` | Login or registration               | Treat as limiter dependency outage; retain state and request id.      | Any persistent or widespread `503` pattern.            |

## Required Incident Artifact

- Frontend route path
- Static endpoint template (if API-related)
- Error code
- `request_id` (if available)
- User-visible message text
- Browser/runtime context

Before sharing the artifact, review it for raw URLs, queries, fragments, request bodies, credentials,
and personal data. Remove any such value rather than attempting partial masking.

## References

- Event schema: `docs/operations/observability_events.md`
- Runtime pipeline: `docs/operations/runtime_error_pipeline.md`
- API consumer matrix: `docs/operations/api_consumer_matrix.md`
