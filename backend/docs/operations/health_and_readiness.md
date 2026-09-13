# Health and Readiness

## Runtime Contract

`GET /v1/health` is public, inexpensive liveness. It reports only that the API process can answer a
request and never resolves settings, database sessions, or external dependencies.

`GET /v1/readiness` is public and intended for traffic admission. Its typed response is:

```json
{
  "status": "ok",
  "checks": [{"name": "database", "status": "ok"}]
}
```

The endpoint returns `200` only when every registered check is `ok`; otherwise it returns `503`
with `status` and affected checks set to `unavailable`. Check names are stable lowercase
snake_case and results are ordered alphabetically. Responses never include URLs, credentials,
exception text, hosts, ports, or provider payloads.

## Registry and Execution

The dependency graph in `app/core/setup/dependencies.py` always registers the configured primary
database as `database`. Enabled capabilities add their own checks through
`ReadinessCheckRegistry`; disabled capabilities have no check and no runtime cost.

When authentication rate limiting uses shared Redis, the registry adds a stable `redis` check that
uses the same lazy client as request enforcement. Memory or disabled local modes do not register
Redis. A failed Redis check marks readiness unavailable without exposing its URL, credentials, or
exception text.

`ReadinessService` runs checks concurrently with a semaphore and applies the configured timeout to
each check after it acquires a slot. Defaults and validation bounds are:

| Variable                    | Default | Valid range                    | Meaning                     |
| --------------------------- | ------- | ------------------------------ | --------------------------- |
| `READINESS_TIMEOUT_SECONDS` | `2`     | greater than `0`, at most `30` | timeout per executing check |
| `READINESS_MAX_CONCURRENCY` | `4`     | `1` through `32`               | maximum simultaneous checks |

The router consumes the typed service dependency and does not instantiate settings or providers.

## Database and Deployment Policy

The database probe opens a short-lived session against the same configured SQLAlchemy session
factory as application traffic and executes only `SELECT 1`. SQLite or PostgreSQL may be used in
`local`, `test`, and `development` outside Compose. `staging` and `production` require PostgreSQL.
Compose also sets `DB_REQUIRE_POSTGRESQL=true`, so a SQLite override fails configuration rather than
appearing ready.

The backend container healthcheck remains on `/v1/health`. An orchestrator or load balancer may use
`/v1/readiness` to admit or remove traffic, but it must not use readiness failures to restart the
process. A dependency outage can therefore drain traffic without creating a restart loop.
