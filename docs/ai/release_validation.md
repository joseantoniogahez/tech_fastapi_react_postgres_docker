# Hosted Release Validation

The `Release validation` workflow in `.github/workflows/release-validation.yaml` validates a clean
template snapshot and a disposable application derived from that snapshot. It runs on pull requests
and can be started from **Actions > Release validation > Run workflow**, selecting the intended
branch. Manual dispatch becomes available after the workflow exists on the default branch.

## Runtime And Ownership

The runner uses the exact Ubuntu, Python, Node, npm, Docker, and Compose versions documented in
[Python tooling](python_tooling.md), including native platform locks. The workflow has read-only
repository permissions, persists no checkout credentials, and needs no application secrets.

`scripts/release_validation.py` requires GitHub Actions on Linux and rejects local invocation before
starting commands or containers. Use the normal local gates in the root README for development.
The workflow owns randomly named containers and a private network, generates disposable credentials,
and removes its services after validation. No deployed application or persistent database is used.

## Checks

- Apply migrations and verify production liveness/readiness with PostgreSQL and authenticated Redis.
- Exercise Redis rate-limit sharing, dependency outages, recovery, and fail-closed login behavior.
- Create a synthetic PostgreSQL backup, check its checksum, restore to an isolated database, and
  verify data integrity and the migration roundtrip.
- Build both production images; verify backend startup migrations/readiness and frontend HTTP headers.
- Clone the exact candidate into a temporary checkout; verify bootstrap preview makes no changes,
  apply a neutral identity, check provenance, and reject a second bootstrap without mutations.
- Run contracts, backend coverage, types, dependency audits, frontend quality/e2e/build, skills,
  and all five Compose render forms in the derived application; repeat its service and image checks.

The workflow validates the checked-out commit, including the merge candidate used by a pull request.
Changes to the candidate require a new run. In an application that already has
`docs/ai/template_provenance.json`, the workflow runs its service and image checks and skips creating
another bootstrapped fixture. Normal CI continues to run the application's contracts, backend, and
frontend gates. The bootstrap contract deliberately refuses a second identity transformation.

## Source Repository And Results

The workflow sets `RELEASE_SOURCE_REPOSITORY` from the current GitHub server and repository. The
helper also accepts `--source-repository` as an explicit override and otherwise derives the URL from
`GITHUB_SERVER_URL` and `GITHUB_REPOSITORY`. Source URLs must be credential-free HTTP(S), with no
query or fragment. The source revision is always the exact checked-out commit.

The job log records candidate/derived commit and tree hashes, generated provenance, image IDs,
restore checksums, and validation results. Keep run links and outcomes in the PR or release record;
do not commit generated reports to the template. Generated credentials are redacted from command
diagnostics. Failed derived fixtures remain in the disposable runner's temporary directory until
runner disposal; recovery artifacts are not automatically discarded on failure.
