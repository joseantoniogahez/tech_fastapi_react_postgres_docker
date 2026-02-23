# Authentication and Account Management

## Endpoints

- `POST /token`
- `POST /users/register`
- `GET /users/me`
- `PATCH /users/me`

## `POST /token` example

Success:

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

```json
{
  "access_token": "s3cr3t-token-value",
  "token_type": "bearer"
}
```

Failure (`401 Unauthorized`):

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=wrong-password"
```

```json
{
  "detail": "Invalid username or password",
  "status": 401,
  "code": "unauthorized"
}
```

## Protected endpoint example (`GET /users/me`)

```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "id": 1,
  "username": "admin",
  "disabled": false
}
```

## Username and Password Rules

- Username normalization: trim + lowercase.
- Username regex: `^[a-z0-9_.-]+$`.
- Password policy (registration and password updates):
  - at least 8 chars
  - at least one lowercase letter
  - at least one uppercase letter
  - at least one number
  - cannot contain the username

## Auth Error Cases

- `401 Unauthorized`
  - Invalid JWT (malformed, expired, wrong signature/algorithm)
  - JWT subject (`sub`) does not exist
  - Invalid login username/password

```json
{
  "detail": "Could not validate credentials",
  "status": 401,
  "code": "unauthorized"
}
```

- `403 Forbidden` (`disabled=true`)

```json
{
  "detail": "Inactive user",
  "status": 403,
  "code": "forbidden"
}
```

- `403 Forbidden` (missing permission)

```json
{
  "detail": "Missing required permission: books:create",
  "status": 403,
  "code": "forbidden",
  "meta": {
    "permission_id": "books:create"
  }
}
```

## RBAC Matrix

See `authorization_matrix.md` for permission-to-endpoint mapping.
