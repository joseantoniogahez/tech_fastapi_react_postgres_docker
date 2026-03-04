# Domain Error -> HTTP Status

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
- FastAPI request validation errors are converted to `400 invalid_input`.
- API request completion logs include a consistent structured shape with `request_id`, `method`, `path`, `status_code`, and `duration_ms`.

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

| Domain Error Code | HTTP Status                 |
| ----------------- | --------------------------- |
| `invalid_input`   | `400 Bad Request`           |
| `unauthorized`    | `401 Unauthorized`          |
| `forbidden`       | `403 Forbidden`             |
| `not_found`       | `404 Not Found`             |
| `conflict`        | `409 Conflict`              |
| `internal_error`  | `500 Internal Server Error` |
