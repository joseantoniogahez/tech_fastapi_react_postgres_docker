# Domain Error -> HTTP Status

For implementation rules and extension workflows, see `../backend_playbook.md`.

## Standard Error Payload

Backend exception handlers return a normalized payload:

```json
{
  "detail": "Human-readable message",
  "status": 400,
  "code": "invalid_input",
  "meta": {},
  "request_id": "a3d5a4c8f1f54c2dbf4d0b7f95b29662"
}
```

Notes:

- `meta` is optional and only appears when extra context is available.
- `request_id` is always included in normalized error payloads.
- The same value is also returned in the `X-Request-ID` response header.
- `401` responses include `WWW-Authenticate: Bearer`.
- `429 rate_limited` includes numeric `X-RateLimit-Limit`, `X-RateLimit-Remaining`,
  `X-RateLimit-Reset`, and `Retry-After` headers.
- `503 service_unavailable` on an authentication surface means the required shared limiter store
  failed closed; it is distinct from an exhausted quota.
- FastAPI request validation errors are converted to `400 invalid_input`.
- API request completion logs include a consistent structured shape with `request_id`, `method`, `path`, `status_code`, and `duration_ms`.
- Authorization decisions are logged as `event=api_authorization_decision` with `request_id`, `user_id`, `permission_id`, `required_scope`, `decision`, `method`, `path`, and `route`.

## Correlation And Log Safety

- An incoming `X-Request-ID` is reused only when it is 1-64 ASCII characters, starts with a letter
  or digit, and otherwise contains letters, digits, `.`, `_`, or `-`. Missing or invalid values are
  replaced with a generated UUID hex value.
- The accepted/generated value is shared by response headers, normalized error bodies,
  authorization decisions, and request-completion logs.
- Request logs record the direct ASGI peer from `request.client.host`. Application code never parses
  `Forwarded` or `X-Forwarded-For`; deployments that require an original client IP must configure a
  named trusted proxy at the ASGI boundary.
- Dynamic log text escapes controls and is bounded to 256 input characters. Structured containers
  are bounded to 50 items and six recursive levels. Token, secret, password, API-key,
  authorization, and cookie key variants are redacted recursively without flattening structure.
- Request/response bodies, credentials, authorization values, and sensitive query values are not
  logged. `event` and `layer` are supplied by code, never by request data.

Example of normalized validation error:

```json
{
  "detail": "Request validation error",
  "status": 400,
  "code": "invalid_input",
  "request_id": "a3d5a4c8f1f54c2dbf4d0b7f95b29662",
  "meta": [
    {
      "loc": ["body", "username"],
      "msg": "Field required"
    }
  ]
}
```

## Domain Error Code Mapping

| Domain Error Code     | HTTP Status                 |
| --------------------- | --------------------------- |
| `invalid_input`       | `400 Bad Request`           |
| `unauthorized`        | `401 Unauthorized`          |
| `forbidden`           | `403 Forbidden`             |
| `not_found`           | `404 Not Found`             |
| `conflict`            | `409 Conflict`              |
| `rate_limited`        | `429 Too Many Requests`     |
| `service_unavailable` | `503 Service Unavailable`   |
| `internal_error`      | `500 Internal Server Error` |
