# Template Reuse Contract

## Purpose

This foundation may seed one new application from an immutable, compatible snapshot. Bootstrap is
a one-time identity transformation, not an idempotent rebranding tool and not a claim that the
result remains the pristine template.

## Compatible Snapshot Boundary

Before preview or write:

1. clone or branch the intended template snapshot into a new, clean checkout;
1. record the credential-free HTTP(S) source repository URL and either a full 40-character commit
   or an existing reviewed tag; mutable branches and symbolic revisions are not accepted;
1. require that revision to resolve locally to the checkout's exact 40-character `HEAD` commit;
1. require a clean Git status and the original critical identity tokens;
1. review newer template snapshots separately rather than assuming compatibility.

The script records both full commit and tree hashes. A matching historical tree may prove content
equivalence, but the recorded commit remains the application's immutable origin coordinate.

## One-Time Transaction And Failure Recovery

`scripts/bootstrap_new_app.py` previews by default and performs exact replacements only. With
`--write`, it stages every output and begins its sequential file commit only after whole-batch
preflight succeeds. Existing destinations move to recoverable backups. A destination that changes or
appears after preflight is rejected without overwrite; a target that wins an exclusive-create race
is preserved. A captured late failure attempts to restore every previous destination.

The commit loop revalidates each destination and installs staged files without overwriting a target
that appears concurrently. The repository root, transaction directory, and each destination must
use a compatible same-filesystem layout with hardlink and same-filesystem replacement support. New
files honor the process umask on POSIX. Replacements preserve the previous POSIX mode
when one existed and are created beside the destination so Windows uses the destination directory's
normal inherited ACL, not the transaction directory's security descriptor. A compatible snapshot
must therefore use normal inherited Windows ACLs; bootstrap does not promise to copy an explicit
per-file DACL. Rollback also refuses to overwrite a target that appears during restoration and
continues across independent destinations.

This is an exception-recovery transaction, not a crash-atomic filesystem transaction. `SIGKILL`,
power loss, or process termination that cannot be caught may interrupt the sequential commit. If
rollback or cleanup cannot complete safely, the script stops, retains the `.bootstrap-*` transaction,
backups, and any reported adjacent `.bootstrap-install-*` file for manual recovery, and refuses to
claim restoration completed. Do not rerun or delete that recovery data until every affected path has
been reviewed.

Successful write creates `docs/ai/template_provenance.json`. Its presence rejects every later
bootstrap attempt. Rename or identity changes to an existing application require a separately
reviewed migration procedure; deleting or editing provenance does not make an application pristine.

## Per-Application Provenance

The generated JSON records:

- provenance schema and template-contract versions;
- source repository, requested revision, resolved commit, and tree;
- UTC bootstrap timestamp;
- application name/slug, frontend package, Compose projects, and JWT issuer/audience;
- an explicit notice that the application is derived rather than pristine.

Commit this small metadata artifact with the application. It contains no credentials, checkout
paths, user identity, source diff, or secret values.

## Rollback And Recovery

Before committing the bootstrap result, rollback is the script's attempted whole-batch restore for
captured failures or discarding the verified temporary checkout. After an abrupt termination or an
incomplete rollback diagnostic, stop and inspect the retained transaction/backups before any manual
recovery. After commit, use a normal reviewed Git revert of the complete bootstrap change. Never
rerun bootstrap over a partially created or established application.

## Validation Boundary

The bootstrap contract suite uses only temporary Git repositories. It proves preview zero-write behavior, incompatible
tokens, revision/dirty-tree rejection, consistent identity/provenance on write, second-run refusal,
post-preflight destination changes, exclusive creation of new targets, restoration after a late
failure or catchable interrupt, adjacent install-source ACL behavior, POSIX umask/mode preservation,
safe concurrent collisions, and retained recovery data after an injected restore failure. No test
writes to this template checkout or a user project. Abrupt process or machine failure remains a
manual-recovery boundary rather than a simulated atomicity claim.
