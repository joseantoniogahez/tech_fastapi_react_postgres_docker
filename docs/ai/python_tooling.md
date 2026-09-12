# Reproducible Python Tooling

This document is the installation and audit contract for the repository root `.venv`. Run every
local Python command through that environment after creating it, as required by `AGENTS.md`.

## Governed Artifacts

- `requirements.txt` is the direct root manifest and includes backend runtime/test manifests.
- `pylock.windows-x86_64.toml` is the complete Windows CPython 3.14.6 resolution. Its 82 packages
  have exact versions, artifact URLs, and SHA-256 hashes.
- `pylock.ubuntu-x86_64.toml` is the complete Ubuntu 24.04 x86_64 CPython 3.14.6 resolution.
- `python-tooling-lock.json` records the lock generator, installer, platforms, input checksums, lock
  checksums, package counts, and Linux validation results.
- `.pre-commit-config.yaml` pins hook revisions and additional hook dependencies. Its commands and
  pins have direct semantic contract tests; it is not an input to either platform `pip lock`. The
  mypy hook mirrors every direct backend and backend-test requirement. Because pre-commit's managed
  Node environment still invokes an npm option removed in npm 12, markdownlint runs as a local
  system hook from the exact `frontend/package-lock.json` development dependency instead.

`pip lock` remains experimental. Its official documentation states that a generated lock is only
guaranteed for the current Python version and platform. Therefore a Windows lock must never be used
as an Ubuntu install source. Generate the Ubuntu lock on Ubuntu 24.04 x86_64 with the
CPython 3.14.6 distribution used by `actions/setup-python`, then verify a clean installation,
dependency consistency, and the vulnerability audit. Before any cache restore or locked install, every CI job runs
the standard-library metadata verifier. It recomputes governed input and platform-lock checksums,
recounts packages, and requires the Ubuntu status and exact proof fields to remain validated.

## Accepted Runner Matrix

| Component       | Windows local lane                           | Ubuntu CI lane                       |
| --------------- | -------------------------------------------- | ------------------------------------ |
| OS/architecture | Windows 11 `10.0.26200`, x64                 | Ubuntu 24.04, x86_64                 |
| Python          | CPython `3.14.6`                             | CPython `3.14.6`                     |
| Node            | `22.23.1`                                    | `22.23.1`                            |
| npm             | contract `12.0.x`, pin `12.0.1`              | contract `12.0.x`, pin `12.0.1`      |
| Browser         | Playwright `1.58.2`, Chromium `145.0.7632.6` | same Playwright-managed pair         |
| Docker          | CLI/Engine `29.6.2`, Compose `5.3.1`         | CLI/Engine `29.6.2`, Compose `5.3.1` |

The accepted npm contract is the `12.0.x` line. Local, Docker, and CI execution use the exact
`12.0.1` pin so that the broader compatibility contract does not weaken reproducibility.
The frontend permits only the reviewed `esbuild@0.27.3` install script and enables npm's strict
install-script policy, so a new unreviewed dependency script fails the install instead of being
silently skipped.
Use `npm --prefix frontend approve-scripts --allow-scripts-pending --json` as the read-only review
command; its `allowScripts` array must be empty before accepting a lockfile change.
CI independently verifies Docker client and server versions and fails on matrix drift.

Pre-commit stages are intentionally disjoint. Fast formatting, lint, Compose, and metadata hooks
default to `pre-commit`; only frontend type checking, Bandit, and mypy run at `pre-push`. CI invokes
both stages over all files without rerunning commit-time hooks during the pre-push stage.

## Root Environment Inventory

| Distribution/import or executable   | Invocation or owner                             | Purpose                                                       |
| ----------------------------------- | ----------------------------------------------- | ------------------------------------------------------------- |
| `pip`                               | root `.venv`, `-m pip`                          | exact bootstrap, lock installation, and `pip check`           |
| `pre-commit` / `pre_commit`         | root `.venv`, `-m pre_commit`                   | repository hook runner and hook installation                  |
| `flake8-pyproject` / `flake8`       | root `.venv`, `-m flake8`                       | Flake8 executable with `pyproject.toml` configuration support |
| `mypy`                              | root `.venv`, `-m mypy`                         | backend and script type checking; matches hook `v1.20.2`      |
| `pip-audit` / `pip_audit`           | root `.venv`, `-m pip_audit`                    | installed-environment vulnerability audit                     |
| `pytest`, `pytest-cov`              | root `.venv`, `-m pytest`                       | contract, unit, integration, and coverage gates               |
| backend/test direct pins            | imports under `backend/app` and `backend/tests` | runtime and test support used from the same root environment  |
| standard-library governance scripts | direct script path through root Python          | scaffold, bootstrap, skill validation, and skill installation |

Remote Python hooks use pre-commit's isolated environments. The `mdformat-gfm` additional
dependency is pinned to `1.0.0`; all other Python hook environments use immutable repository
revisions. Local system hooks intentionally use the audited Node/npm and Docker tools, not packages
from `.venv`. The markdownlint system hook resolves exact `markdownlint-cli` `0.48.0` from the
frontend lock and therefore does not ask pre-commit to create a Node environment with npm's removed
`--ignore-prepublish` option.

Add providers, AI SDKs, document-processing libraries, or job queues only for a concrete application
requirement, with explicit ownership and validation; they are not part of the base profile.

## Clean Windows Installation

Install CPython 3.14.6 first, then run from the repository root. Creating `.venv` is the documented
bootstrap exception; every later Python command uses that environment explicitly.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -c "import sys; assert sys.version_info[:3] == (3, 14, 6)"
.\.venv\Scripts\python.exe -m pip install pip==26.2.1
.\.venv\Scripts\python.exe scripts\update_python_tooling_lock.py
.\.venv\Scripts\python.exe -m pip install --requirement pylock.windows-x86_64.toml
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip_audit --local
```

Regenerate only on the accepted Windows lane, using the exact generator recorded in metadata:

```powershell
.\.venv\Scripts\python.exe -m pip install pip==26.0.1
.\.venv\Scripts\python.exe -m pip lock --requirement requirements.txt --output pylock.windows-x86_64.toml
.\.venv\Scripts\python.exe -m pip install pip==26.2.1
```

Refresh and review governed checksums and package counts after an intentional input or lock change:

```powershell
.\.venv\Scripts\python.exe scripts\update_python_tooling_lock.py --write
```

Without `--write`, the command is a read-only check and also requires `ci_lock.status=validated`
plus the exact clean-install, `pip check`, and `pip-audit` pass proof. `--write` updates hashes and
package counts. A Windows-lock-only refresh preserves Ubuntu proof; a governed input or Ubuntu-lock
change sets the Ubuntu status and all proof fields to `pending`. After such invalidation, regenerate
and prove the Ubuntu lock before restoring the reviewed `validated`/`pass` fields. The
`python-tooling-lock-check` pre-commit hook runs the read-only verifier whenever a governed manifest,
platform lock, metadata file, or checksum script is staged.

## Clean POSIX/Ubuntu Installation

The Ubuntu lock must be generated and installed on Ubuntu 24.04 x86_64. These are the exact
regeneration commands. Record its SHA-256 and package count in `python-tooling-lock.json` only after
every command passes.

```bash
python3.14 -m venv .venv
./.venv/bin/python -c 'import sys; assert sys.version_info[:3] == (3, 14, 6)'
./.venv/bin/python -m pip install pip==26.0.1
./.venv/bin/python -m pip lock --requirement requirements.txt --output pylock.ubuntu-x86_64.toml
./.venv/bin/python -m pip install pip==26.2.1
./.venv/bin/python -m pip install --requirement pylock.ubuntu-x86_64.toml
./.venv/bin/python -m pip check
./.venv/bin/python -m pip_audit --local
./.venv/bin/python scripts/update_python_tooling_lock.py --write
```

The write refresh intentionally leaves Ubuntu proof `pending` after an input or Ubuntu-lock change.
Review the new input hashes, lock SHA-256, package count, and the successful commands above before
restoring `status: validated` and the three `pass` proof values in metadata. Then run the verifier
without `--write`; CI uses that same command before consuming the lock.

## Validation Commands

Windows:

```powershell
.\.venv\Scripts\python.exe -m mypy backend
.\.venv\Scripts\python.exe -m pytest backend\tests
.\.venv\Scripts\python.exe -m pre_commit run --all-files
```

POSIX:

```bash
./.venv/bin/python -m mypy backend
./.venv/bin/python -m pytest backend/tests
./.venv/bin/python -m pre_commit run --all-files
```

## Dependency Maintenance

The manifests and platform locks are authoritative for current package versions. Tests use
`httpx2==2.12.0` and its HTTPCore2 dependency as the Starlette test client; this does not add an
application HTTP client.

For a dependency repair, review compatibility and upstream advisories, regenerate both locks on
their native platforms, and preserve unrelated resolutions where possible. Require fresh clean
installation, `pip check`, and audit results before accepting the Ubuntu validation fields. Record
the results in the change's CI run or PR; a prior passing audit does not establish current safety.

## Official References

- [pip lock command](https://pip.pypa.io/en/stable/cli/pip_lock/)
- [PEP 751 pylock specification](https://packaging.python.org/en/latest/specifications/pylock-toml/)
- [FastAPI 0.133.0 metadata](https://pypi.org/pypi/fastapi/0.133.0/json)
- [Pydantic Settings advisory](https://github.com/pydantic/pydantic-settings/security/advisories/GHSA-4xgf-cpjx-pc3j)
- [PyJWT releases](https://pypi.org/project/PyJWT/)
- [pytest releases](https://pypi.org/project/pytest/)
- [python-multipart releases](https://pypi.org/project/python-multipart/)
- [Starlette TestClient](https://www.starlette.io/testclient/)
- [HTTPX2 releases](https://pypi.org/project/httpx2/)
- [React Router advisory](https://github.com/advisories/GHSA-qwww-vcr4-c8h2)
