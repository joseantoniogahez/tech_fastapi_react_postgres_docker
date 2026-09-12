# Authentication Rate Limiting

## Protected Surfaces And Quotas

The backend applies a fixed-window limit before processing these public authentication writes:

| Surface    | Endpoint                  | Default limit | Default window |
| ---------- | ------------------------- | ------------- | -------------- |
| `login`    | `POST /v1/token`          | 10 requests   | 60 seconds     |
| `register` | `POST /v1/users/register` | 5 requests    | 60 seconds     |

Every permitted response includes numeric `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and
`X-RateLimit-Reset` headers. Reset is the number of whole seconds until the fixed window expires.
An excess request returns normalized `429 rate_limited`, adds numeric `Retry-After`, and does not
invoke authentication or registration logic.

## Identity And Privacy Boundary

The counter identity is a namespaced SHA-256 digest of only the stable surface name and the direct
ASGI peer at `request.client.host`. It never contains or derives from a username, email, password,
request body, query value, `Forwarded`, or `X-Forwarded-For`. Deployments needing the original
client address must configure an explicitly trusted proxy at the ASGI boundary; application code
does not parse forwarding headers.

Logs contain only code-owned event names, `request_id`, and the neutral surface name. Counter keys,
peer addresses, credentials, bodies, and provider exceptions are not logged.

## Environment And Store Policy

Local, test, and development default to an enabled in-memory store and may explicitly set
`RATE_LIMIT_ENABLED=false`. Memory state is process-local and is not suitable for horizontally
scaled enforcement.

Staging and production require all enablement, thresholds, window, Redis URL, and authentication
settings to be explicit. They reject a disabled limiter or memory store. Non-Compose Redis must use
`rediss://`; `redis://` is accepted only with the explicit `REDIS_ALLOW_PLAINTEXT=true` transport
exception for a private network.

Compose pins `redis:8.8.1-alpine`, publishes no Redis port, requires password authentication from a
Compose secret backed by `REDIS_PASSWORD`, and explicitly permits plaintext only on its private
service network. `docker compose config` renders the secret source name and mount, not its value.
The backend reads the mounted password through `REDIS_PASSWORD_FILE`.

## Atomicity, Lifecycle, Readiness, And Failure

Redis enforcement uses one Lua evaluation containing `INCR`, first-write `EXPIRE`, and `TTL`; the
increment and expiry decision are atomic. The Redis client is created lazily, shared for request
enforcement and readiness, and closed with `aclose()` during application lifespan shutdown. Both
connection establishment and Redis commands use the bounded `REDIS_TIMEOUT_SECONDS` timeout, so a
network outage cannot leave an authentication request waiting indefinitely.

Enabled shared Redis registers the stable readiness dependency `redis`. A Redis command failure on
either protected surface fails closed as normalized `503 service_unavailable` with dependency name
`rate_limit_store`; it never silently bypasses enforcement. This is operationally distinct from
`429 rate_limited`, which means Redis or memory was available and the quota was exhausted.

## Configuration

| Variable                    | Local default              | Contract                                                       |
| --------------------------- | -------------------------- | -------------------------------------------------------------- |
| `RATE_LIMIT_ENABLED`        | `true`                     | mandatory `true` in staging/production                         |
| `RATE_LIMIT_STORAGE`        | `memory`                   | `memory` or `redis`; mandatory `redis` in staging/production   |
| `RATE_LIMIT_LOGIN`          | `10`                       | positive integer; explicit in staging/production               |
| `RATE_LIMIT_REGISTER`       | `5`                        | positive integer; explicit in staging/production               |
| `RATE_LIMIT_WINDOW_SECONDS` | `60`                       | positive integer up to one day; explicit in staging/production |
| `RATE_LIMIT_NAMESPACE`      | `foundation:rate-limit:v1` | neutral lowercase namespace                                    |
| `REDIS_URL`                 | unset                      | credential-free `redis://` or `rediss://` URL                  |
| `REDIS_PASSWORD`            | unset                      | direct secret for non-Compose deployment                       |
| `REDIS_PASSWORD_FILE`       | unset                      | mutually exclusive mounted secret file                         |
| `REDIS_ALLOW_PLAINTEXT`     | `false`                    | explicit exception required for `redis://`                     |
| `REDIS_TIMEOUT_SECONDS`     | `2`                        | connection and command timeout; greater than 0, at most 30     |
