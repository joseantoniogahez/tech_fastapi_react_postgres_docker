# PostgreSQL Backup And Restore

## Scope And Ownership

This is a manual operator runbook for PostgreSQL deployments of the foundation. It does not claim
that backups are scheduled, uploaded, encrypted, retained, or monitored by this repository. A dump
is not a verified recovery point until an isolated restore drill passes.

Before operating a deployment, fill and approve this policy record:

| Required field                      | Approved value                                      |
| ----------------------------------- | --------------------------------------------------- |
| Environment and database            | `<required>`                                        |
| Operator and approving owner        | `<required>`                                        |
| Recovery point objective (RPO)      | `<required duration>`                               |
| Recovery time objective (RTO)       | `<required duration>`                               |
| Retention and expiry policy         | `<required>`                                        |
| Encrypted external storage          | `<required location identifier; never credentials>` |
| Backup schedule                     | `<required>`                                        |
| Restore-drill cadence               | `<required>`                                        |
| Encryption/key-management authority | `<required; outside this repository>`               |

Stop and escalate when any field is missing. The operator owns scheduling until an external backup
service is selected and proven.

## Evidence Record

For every dump and drill, retain this redacted metadata outside the repository:

- target repository commit and Alembic revision;
- UTC start/end timestamps and operator identity;
- PostgreSQL server version and `pg_dump`/`pg_restore` client versions;
- environment and non-secret database identifier;
- dump filename, byte size, SHA-256 checksum, and encrypted storage object/version identifier;
- RPO/RTO target and observed backup/restore durations;
- integrity queries and expected/actual results;
- restore-drill result, reviewer, expiry, and next scheduled drill;
- incident/ticket identifier for any failure.

Never record connection strings, passwords, tokens, encryption keys, row data, or raw dumps in Git,
CI logs, screenshots, or this evidence record.

## Create A Custom-Format Dump

Run from repository root against the intended Compose project. Use a protected directory outside
the checkout in real operations; `backups/` below is only a portable shell example and is excluded
from Git and image contexts.

```powershell
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$backupDir = Join-Path (Get-Location) "backups"
$backupFile = Join-Path $backupDir "postgres-$stamp.dump"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
docker compose -f compose.yaml -f compose.prod.yaml exec -T database sh -c 'umask 077; pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --format=custom --compress=9 --no-owner --no-privileges --file=/tmp/postgres.dump'
docker compose -f compose.yaml -f compose.prod.yaml cp database:/tmp/postgres.dump $backupFile
docker compose -f compose.yaml -f compose.prod.yaml exec -T database rm -f /tmp/postgres.dump
$checksum = (Get-FileHash -Algorithm SHA256 -LiteralPath $backupFile).Hash.ToLowerInvariant()
$size = (Get-Item -LiteralPath $backupFile).Length
"$checksum  $([IO.Path]::GetFileName($backupFile))" | Set-Content -Encoding ascii "$backupFile.sha256"
```

Require every command to succeed, require a non-empty file, record the size and checksum, then
encrypt and transfer the dump using the operator-approved system. Encryption keys and credentials
must stay outside the host and repository. Verify the external object's checksum after transfer.

## Restore Drill In Isolation

Never restore into the source or production database. Use a separately named database with no
application connections, verify the checksum before copying, and reject version incompatibilities.

```powershell
$restoreDb = "foundation_restore_$((Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmss'))"
$expectedChecksum = (Get-Content -LiteralPath "$backupFile.sha256").Split(' ')[0]
$actualChecksum = (Get-FileHash -Algorithm SHA256 -LiteralPath $backupFile).Hash.ToLowerInvariant()
if ($actualChecksum -ne $expectedChecksum) { throw "Backup checksum mismatch" }
docker compose -f compose.yaml -f compose.prod.yaml cp $backupFile database:/tmp/postgres.dump
docker compose -f compose.yaml -f compose.prod.yaml exec -T --env RESTORE_DB=$restoreDb database sh -c 'createdb --username="$POSTGRES_USER" "$RESTORE_DB" && pg_restore --username="$POSTGRES_USER" --dbname="$RESTORE_DB" --exit-on-error --no-owner --no-privileges /tmp/postgres.dump'
docker compose -f compose.yaml -f compose.prod.yaml exec -T --env RESTORE_DB=$restoreDb database sh -c 'test "$(psql --username="$POSTGRES_USER" --dbname="$RESTORE_DB" --tuples-only --no-align --command="SELECT count(*) FROM alembic_version;")" = "1"'
docker compose -f compose.yaml -f compose.prod.yaml exec -T --env RESTORE_DB=$restoreDb database sh -c 'dropdb --username="$POSTGRES_USER" --if-exists "$RESTORE_DB"; rm -f /tmp/postgres.dump'
```

The drill passes only when `pg_restore --exit-on-error` succeeds, the Alembic revision exists, and
the owner-approved integrity and application smoke queries match recorded expectations. Measure
elapsed restore time against RTO. Clean up the isolated database and container copy after evidence
is retained; do not delete the encrypted recovery point before its approved expiry.

## Recovery And Failure Handling

- If dump, checksum, encryption, or transfer fails, quarantine or delete only the incomplete local
  artifact and create a new dump. Never label it successful.
- If a restore drill fails, preserve the encrypted source under access control, open an incident,
  create a new candidate, and block destructive maintenance that depends on recovery.
- Before a real restore, stop writers, obtain explicit authorization, make and verify an emergency
  pre-restore backup, record the rollback point, and confirm version compatibility.
- After restore, run Alembic migrations only under the approved release procedure, then readiness,
  backend tests/smoke checks, and data-integrity queries before admitting traffic.
- Never use `docker compose down -v`, drop a database, or delete a volume unless a verified,
  encrypted recovery point and successful restore drill meet the approved RPO/RTO. `down -v`
  irreversibly deletes Compose-managed database data.

## Completion Checklist

- [ ] Policy fields, operator, and approvals are complete.
- [ ] Custom-format dump completed with pinned client/server versions recorded.
- [ ] File is non-empty and SHA-256 matches the encrypted external copy.
- [ ] Repository commit, Alembic revision, UTC timestamps, sizes, and durations are recorded.
- [ ] Isolated restore and owner-approved integrity checks passed within RTO.
- [ ] No secret, raw data, or dump entered source control, build contexts, or logs.
- [ ] Retention expiry and next restore-drill date are recorded.
