# Authentication and Account Management

For implementation rules and extension workflows, see `../backend_playbook.md`.

## Endpoints

- `POST /v1/token`
- `POST /v1/users/register`
- `GET /v1/users/me`
- `PATCH /v1/users/me`
- `DELETE /v1/rbac/users/{user_id}` (admin soft delete, sets `disabled=true`)

## Bootstrap Admin User (Fresh Environments)

Run the idempotent RBAC bootstrap command from `backend/`:

```bash
python -m utils.rbac_bootstrap --admin-username admin --admin-password "StrongSeed9"
```

This command:

- syncs base permissions and roles,
- creates the admin user only if missing, and
- ensures admin role assignment.

## Authentication Flow

1. Run RBAC bootstrap to create/sync base auth data (including admin user when missing).
1. Exchange credentials for a bearer token with `POST /v1/token`.
1. Call protected endpoints with `Authorization: Bearer <access_token>`.

Access tokens now include:

- standard claims `sub`, `iss`, `aud`, `iat`, `exp`, and `jti`,
- a custom `rbac_version` claim derived from the caller's current effective permissions (including inherited roles).

In plain terms:

- `iss` tells who created the token.
- `aud` tells which API the token is meant for.
- `iat` tells when the token was issued.
- `jti` gives that specific token its own unique id.

`iss` and `aud` are checked when the token is decoded, so the API does not accept a token created for a different issuer or audience.

`rbac_version` is how the API handles early token invalidation after RBAC changes.

- At login time, the backend calculates a stable hash of the user's current effective permissions (direct + inherited roles).
- That hash is stored inside the token as `rbac_version`.
- On each authenticated request, the backend calculates the current hash again.
- If the stored value and the current value do not match, the token is rejected.

This means a token can become invalid before `exp` when the user's roles or permissions change. In practice, if an admin removes or changes a user's access, older tokens stop working and the user must log in again.

## Scoped Authorization

Permission checks support scopes:

- `own`: self-service resources owned by the authenticated user.
- `tenant`: resources within the authenticated user's tenant.
- `any`: global access (typically admin-level).

Evaluation is deterministic and handled in `AuthService.user_has_permission(...)`:

- Scope ordering is `own < tenant < any`.
- Required `any` accepts only granted `any`.
- Required `tenant` accepts granted `tenant` (with tenant match) or `any`.
- Required `own` accepts granted `own` (owner match), granted `tenant` (owner or tenant match), or `any`.
- Missing required context (`resource_owner_id` / `resource_tenant_id`) resolves to deny.
- Within a single HTTP request, permission grant lookups are memoized by `(user_id, permission_id)` to avoid repeated repository reads when multiple dependencies enforce the same permission.

## `POST /v1/token` Example

Success:

```bash
curl -X POST http://localhost:8000/v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=<admin_password>"
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

The JWT payload contains `sub`, `iss`, `aud`, `iat`, `exp`, `jti`, and `rbac_version`, even though the API only returns the encoded bearer token string to clients.

Invalid credentials (`401 Unauthorized`):

```bash
curl -X POST http://localhost:8000/v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=wrong-password"
```

```json
{
  "detail": "Invalid username or password",
  "status": 401,
  "code": "unauthorized",
  "request_id": "req-example-1234"
}
```

## Protected Endpoint Example (`GET /v1/users/me`)

```bash
curl -X GET http://localhost:8000/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

```json
{
  "id": 1,
  "username": "admin",
  "disabled": false,
  "permissions": [
    "role_permissions:manage",
    "roles:manage",
    "user_roles:manage",
    "users:manage"
  ]
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

`PATCH /v1/users/me` rules:

- At least one updatable field must be provided.
- `new_password` requires `current_password`.
- `current_password` requires `new_password`.
- New password must differ from the current password.

Transactional behavior:

- `POST /v1/users/register` and `PATCH /v1/users/me` run inside Unit of Work transaction scopes.
- On failure, pending account writes are rolled back.
- See `../architecture/unit_of_work.md` for transaction details.

Authenticated user payload behavior:

- `POST /v1/users/register`, `GET /v1/users/me`, and `PATCH /v1/users/me` return
  `{ id, username, disabled, permissions }`.
- `permissions` is derived at read time from effective RBAC grants (direct + inherited roles), deduplicated, and
  sorted for deterministic responses.

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
  "code": "unauthorized",
  "request_id": "req-example-1234"
}
```

`403 Forbidden` (inactive user):

```json
{
  "detail": "Inactive user",
  "status": 403,
  "code": "forbidden",
  "request_id": "req-example-1234"
}
```

Inactive users can be produced by admin soft-delete via `DELETE /v1/rbac/users/{user_id}`.

`403 Forbidden` (missing permission):

```json
{
  "detail": "Missing required permission: role_permissions:manage",
  "status": 403,
  "code": "forbidden",
  "request_id": "req-example-1234",
  "meta": {
    "permission_id": "role_permissions:manage"
  }
}
```

See `authorization_matrix.md` for permission-to-endpoint mapping and required scopes.
