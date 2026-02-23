# Authentication and Account Management

## Endpoints

- `POST /token`
- `POST /users/register`
- `GET /users/me`
- `PATCH /users/me`

## Authentication Flow

1. Create a user with `POST /users/register` (or use a seeded account).
2. Exchange credentials for a bearer token with `POST /token`.
3. Call protected endpoints with `Authorization: Bearer <access_token>`.

## `POST /token` Example

Success:

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Invalid credentials (`401 Unauthorized`):

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

## Protected Endpoint Example (`GET /users/me`)

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

## Registration and Update Rules

Username rules:

- Normalized with trim + lowercase.
- Regex: `^[a-z0-9_.-]+$`.

Password rules (registration and password update):

- At least 8 characters.
- At least one lowercase letter.
- At least one uppercase letter.
- At least one number.
- Cannot contain the username.

`PATCH /users/me` rules:

- At least one updatable field must be provided.
- `new_password` requires `current_password`.
- `current_password` requires `new_password`.
- New password must differ from the current password.

## Common Auth Errors

`401 Unauthorized`:

- Invalid login credentials.
- Missing, invalid, or expired JWT.
- JWT subject user does not exist.
- Invalid `current_password` during profile update.

```json
{
  "detail": "Could not validate credentials",
  "status": 401,
  "code": "unauthorized"
}
```

`403 Forbidden` (inactive user):

```json
{
  "detail": "Inactive user",
  "status": 403,
  "code": "forbidden"
}
```

`403 Forbidden` (missing permission):

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

See `authorization_matrix.md` for permission-to-endpoint mapping.
