# Domain Error -> HTTP Status

## Standard Error Payload

Backend error handlers return a normalized payload:

```json
{
  "detail": "Human-readable message",
  "status": 400,
  "code": "invalid_input",
  "meta": {}
}
```

Notes:

- `meta` is optional and only appears when extra context is available.
- `401` responses include `WWW-Authenticate: Bearer`.

## Domain Error Code Mapping

| Domain Error Code | HTTP Status |
| --- | --- |
| `invalid_input` | `400 Bad Request` |
| `unauthorized` | `401 Unauthorized` |
| `forbidden` | `403 Forbidden` |
| `not_found` | `404 Not Found` |
| `conflict` | `409 Conflict` |
| `internal_error` | `500 Internal Server Error` |
