"""Validate real services, images, and a disposable application on hosted Ubuntu.

This is a release validation helper, never an application entrypoint. It runs only
in GitHub Actions on the approved runner and owns only randomly named containers.
"""

from __future__ import annotations

import json
import hashlib
import argparse
import os
from pathlib import Path
import platform
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.parse import urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SECRET_VALUES: list[str] = []


def run(*args: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> str:
    started = time.monotonic()
    result = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=1800, check=False)
    output = result.stdout
    for value in SECRET_VALUES:
        output = output.replace(value, "[redacted]")
    if result.returncode:
        print(output[-12000:], flush=True)
        raise RuntimeError(f"Validation command {Path(args[0]).name} failed ({result.returncode})")
    print(f"PASS {Path(args[0]).name} {args[1] if len(args) > 1 else ''} "
          f"({time.monotonic() - started:.2f}s)", flush=True)
    return output.strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def wait_command(args: list[str], env: dict[str, str] | None = None) -> None:
    for _ in range(60):
        result = subprocess.run(args, env=env, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=5, check=False)
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("Disposable service did not become ready")


def npm_policy(root: Path) -> None:
    policy = json.loads(run("npm", "--prefix", "frontend", "approve-scripts",
                            "--allow-scripts-pending", "--json", cwd=root))
    require(policy.get("allowScripts") == [], "Unreviewed npm install script")
    print("npm pending allowScripts: []")


def probe() -> None:
    # A subprocess gets a new application/engine per dependency state.
    from starlette.testclient import TestClient
    from app.main import app

    mode = os.environ["RELEASE_PROBE"]
    with TestClient(app) as client:
        require(client.get("/v1/health").status_code == 200, "Liveness depends on services")
        response = client.get("/v1/readiness")
        expected = {"database": "ok", "redis": "ok"}
        if mode != "healthy":
            expected[mode] = "unavailable"
        require(response.status_code == (200 if mode == "healthy" else 503),
                f"Readiness status for {mode}: HTTP {response.status_code}")
        require(response.json() == {
            "status": "ok" if mode == "healthy" else "unavailable",
            "checks": [{"name": key, "status": value} for key, value in sorted(expected.items())],
        }, "Readiness payload")
        if mode == "redis":
            limited = client.post("/v1/token", data={"username": "synthetic", "password": "unused"})
            require(limited.status_code == 503, "Redis outage must fail closed on login")
        require(client.get("/openapi.json").status_code == 404, "Production OpenAPI exposure")
    print(f"production probe {mode}: passed")


def service_gate(root: Path, python: str) -> None:
    suffix = uuid4().hex[:12]
    pg, redis = f"rel-pg-{suffix}", f"rel-redis-{suffix}"
    network = f"rel-net-{suffix}"
    owned: list[str] = []
    password = secrets.token_hex(24)
    SECRET_VALUES.append(password)
    container_env = dict(os.environ, POSTGRES_PASSWORD=password, REDIS_PASSWORD=password,
                         REDISCLI_AUTH=password, PGPASSWORD=password)
    run("docker", "network", "create", network)
    try:
        run("docker", "run", "-d", "--name", pg, "--label", "foundation.release=true",
            "--network", network,
            "--tmpfs", "/var/lib/postgresql", "-p", "127.0.0.1::5432",
            "-e", "POSTGRES_PASSWORD", "-e", "POSTGRES_USER=release_user",
            "-e", "POSTGRES_DB=release_source", "postgres:18.2", env=container_env)
        owned.append(pg)
        run("docker", "run", "-d", "--name", redis, "--label", "foundation.release=true",
            "--network", network,
            "-p", "127.0.0.1::6379", "-e", "REDIS_PASSWORD", "redis:8.8.1-alpine",
            "sh", "-c", 'exec redis-server --appendonly no --requirepass "$REDIS_PASSWORD"',
            env=container_env)
        owned.append(redis)
        for name in owned:
            print(run("docker", "inspect", "--format", "{{.Image}}", name))
        port = lambda name, internal: json.loads(run("docker", "inspect", "--format",
                    "{{json .NetworkSettings.Ports}}", name))[internal][0]["HostPort"]
        pg_port, redis_port = port(pg, "5432/tcp"), port(redis, "6379/tcp")
        pg_wait = ["docker", "exec", "-e", "PGPASSWORD", pg, "psql", "-h", "127.0.0.1",
                   "-U", "release_user", "-d", "release_source", "-Atc", "SELECT 1"]
        redis_wait = ["docker", "exec", "-e", "REDISCLI_AUTH", redis, "redis-cli", "ping"]
        wait_command(pg_wait, container_env)
        wait_command(redis_wait, container_env)
        env = dict(os.environ, PYTHONPATH=str(root / "backend"), APP_ENV="production",
                   DB_TYPE="postgresql+asyncpg", DB_HOST="127.0.0.1", DB_PORT=pg_port,
                   DB_NAME="release_source", DB_USER="release_user", DB_PASSWORD=password,
                   DB_REQUIRE_POSTGRESQL="true", JWT_SECRET_KEY=password, JWT_ALGORITHM="HS256",
                   JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30", JWT_ISSUER="release-validation",
                   JWT_AUDIENCE="release-validation", RATE_LIMIT_ENABLED="true",
                   RATE_LIMIT_STORAGE="redis", RATE_LIMIT_LOGIN="10", RATE_LIMIT_REGISTER="5",
                   RATE_LIMIT_WINDOW_SECONDS="60", REDIS_URL=f"redis://127.0.0.1:{redis_port}/0",
                   REDIS_PASSWORD=password, REDIS_ALLOW_PLAINTEXT="true", REDIS_TIMEOUT_SECONDS="1",
                   READINESS_TIMEOUT_SECONDS="2", LOG_LEVEL="CRITICAL")
        run(python, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head", cwd=root, env=env)
        test_env = dict(os.environ, TEST_REDIS_URL=env["REDIS_URL"], TEST_REDIS_PASSWORD=password)
        print(run(python, "-m", "pytest", "backend/tests/integration/test_rate_limit_redis.py", "-q",
                  cwd=root, env=test_env))
        def health(mode: str) -> None:
            print(run(python, str(root / "scripts/release_validation.py"), "--probe", cwd=root,
                      env=dict(env, RELEASE_PROBE=mode)))
        health("healthy")
        run("docker", "stop", redis)
        health("redis")
        run("docker", "start", redis)
        wait_command(redis_wait, container_env)
        # Docker may allocate a different ephemeral host port after a restart.
        env["REDIS_URL"] = f"redis://127.0.0.1:{port(redis, '6379/tcp')}/0"
        health("healthy")
        run("docker", "pause", pg)
        health("database")
        run("docker", "unpause", pg)
        wait_command(pg_wait, container_env)
        health("healthy")
        def sql(database: str, query: str) -> str:
            return run("docker", "exec", pg, "psql", "-U", "release_user", "-d", database,
                       "-v", "ON_ERROR_STOP=1", "-Atc", query)
        revision = sql("release_source", "SELECT version_num FROM alembic_version")
        sql("release_source", "CREATE TABLE release_probe (value integer PRIMARY KEY); "
            "INSERT INTO release_probe VALUES (1)")
        run("docker", "exec", pg, "pg_dump", "-U", "release_user", "-d", "release_source",
            "-Fc", "--no-owner", "--no-privileges", "-f", "/tmp/release.dump")
        checksum = run("docker", "exec", pg, "sha256sum", "/tmp/release.dump").split()[0]
        size = run("docker", "exec", pg, "stat", "-c", "%s", "/tmp/release.dump")
        require(int(size) > 0, "Empty dump")
        run("docker", "exec", pg, "createdb", "-U", "release_user", "release_restore")
        require(run("docker", "exec", pg, "sha256sum", "/tmp/release.dump").split()[0] == checksum,
                "Dump checksum changed before restore")
        run("docker", "exec", pg, "pg_restore", "-U", "release_user", "-d", "release_restore",
            "--exit-on-error", "--no-owner", "--no-privileges", "/tmp/release.dump")
        require(sql("release_restore", "SELECT version_num FROM alembic_version") == revision,
                "Restored migration revision differs")
        require(sql("release_restore", "SELECT count(*) FROM release_probe WHERE value=1") == "1",
                "Restored synthetic integrity probe differs")
        print(f"RESTORE revision={revision} bytes={size} sha256={checksum}")
        restored_env = dict(env, DB_NAME="release_restore")
        run(python, "-m", "alembic", "-c", "backend/alembic.ini", "downgrade", "base",
            cwd=root, env=restored_env)
        run(python, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head",
            cwd=root, env=restored_env)
        require(sql("release_restore", "SELECT version_num FROM alembic_version") == revision,
                "Migration roundtrip differs")
        api = f"rel-api-{suffix}"
        run("docker", "build", "-t", api, "backend", cwd=root)
        run("docker", "exec", pg, "createdb", "-U", "release_user", "release_image")
        api_env = dict(env, DB_HOST=pg, DB_PORT="5432", DB_NAME="release_image",
                       REDIS_URL=f"redis://{redis}:6379/0")
        names = [key for key in api_env if key.startswith(("DB_", "JWT_", "RATE_LIMIT_", "REDIS_", "READINESS_"))]
        names += ["APP_ENV", "LOG_LEVEL"]
        env_args = [part for name in names for part in ("-e", name)]
        run("docker", "run", "-d", "--name", api, "--network", network,
            "-p", "127.0.0.1::8000", *env_args, api, env=api_env)
        owned.append(api)
        print(run("docker", "image", "inspect", "--format", "{{.Id}}", api))
        api_port = port(api, "8000/tcp")
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{api_port}/v1/readiness", timeout=3) as response:
                    body = json.load(response)
                    require(body == {"status": "ok", "checks": [
                        {"name": "database", "status": "ok"}, {"name": "redis", "status": "ok"}
                    ]}, "Backend image readiness")
                break
            except (OSError, TimeoutError):
                time.sleep(1)
        else:
            raise RuntimeError("Backend production image did not become ready")
        print("Backend image entrypoint and HTTP readiness passed")
        require(sql("release_image", "SELECT version_num FROM alembic_version") == revision,
                "Backend entrypoint did not migrate its fresh database")
    finally:
        for name in reversed(owned):
            run("docker", "rm", "-f", "-v", name)
        run("docker", "network", "rm", network)


def image_gate(root: Path) -> None:
    name = f"rel-ui-{uuid4().hex[:12]}"
    run("docker", "build", "--target", "production", "--build-arg",
        "VITE_API_ORIGIN=https://api.example.test", "--build-arg", "VITE_API_BASE_PATH=/v1",
        "-t", name, "frontend", cwd=root)
    run("docker", "run", "-d", "--name", name, "-p", "127.0.0.1::3000", name)
    try:
        print(run("docker", "image", "inspect", "--format", "{{.Id}}", name))
        bindings = json.loads(run("docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", name))
        origin = f"http://127.0.0.1:{bindings['3000/tcp'][0]['HostPort']}"
        # The smoke helper itself waits for service readiness.
        print(run("node", "frontend/scripts/security-headers-smoke.mjs", origin,
                  "https://api.example.test", cwd=root))
    finally:
        run("docker", "rm", "-f", name)


def resolve_source_repository(override: str | None = None) -> str:
    candidate = override or os.environ.get("RELEASE_SOURCE_REPOSITORY")
    if not candidate:
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        require(bool(repository), "Source repository URL or GITHUB_REPOSITORY required")
        candidate = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com').rstrip('/')}/{repository}"
    candidate = candidate.strip()
    parsed = urlsplit(candidate)
    require(parsed.scheme in {"http", "https"} and bool(parsed.netloc)
            and parsed.username is None and parsed.password is None
            and not parsed.query and not parsed.fragment,
            "Source repository must be a credential-free HTTP(S) URL")
    return candidate.rstrip("/")


def main(source_repository: str | None = None) -> None:
    require(os.environ.get("GITHUB_ACTIONS") == "true", "Hosted release runner required")
    require(platform.system() == "Linux", "Ubuntu release runner required")
    require(platform.python_version() == "3.14.6", "Python matrix drift")
    source_repository = resolve_source_repository(source_repository)
    require(run("docker", "version", "--format", "{{.Client.Version}}/{{.Server.Version}}")
            == "29.6.2/29.6.2", "Docker matrix drift")
    require(run("docker", "compose", "version", "--short") == "5.3.1", "Compose matrix drift")
    require(run("git", "status", "--porcelain") == "", "Candidate checkout must be clean")
    candidate = run("git", "rev-parse", "HEAD")
    candidate_tree = run("git", "rev-parse", "HEAD^{tree}")
    npm_policy(ROOT)
    print(f"CANDIDATE {candidate} TREE {run('git', 'rev-parse', 'HEAD^{tree}')}")
    service_gate(ROOT, sys.executable)
    image_gate(ROOT)
    if (ROOT / "docs/ai/template_provenance.json").exists():
        require(run("git", "status", "--porcelain") == "", "Validation changed tracked candidate")
        print("Hosted service and image gates passed; existing application provenance skips template bootstrap")
        return
    # Retain failed fixtures, including recovery artifacts, until runner disposal/review.
    temp = tempfile.mkdtemp(prefix="rel-derived-", dir=os.environ["RUNNER_TEMP"])
    try:
        derived = Path(temp) / "repo"
        run("git", "clone", "--no-hardlinks", str(ROOT), str(derived))
        run("git", "checkout", "--detach", candidate, cwd=derived)
        run(sys.executable, "-m", "venv", str(derived / ".venv"))
        python = str(derived / ".venv/bin/python")
        run(python, "-m", "pip", "install", "pip==26.2.1", cwd=derived)
        run(python, "scripts/update_python_tooling_lock.py", cwd=derived)
        run(python, "-m", "pip", "install", "-r", "pylock.ubuntu-x86_64.toml", cwd=derived)
        bootstrap = (python, "scripts/bootstrap_new_app.py", "--source-repository", source_repository,
                     "--source-revision", candidate, "--app-name", "Release Fixture Portal",
                     "--description", "A neutral validation fixture.")
        run(*bootstrap, cwd=derived)
        require(run("git", "status", "--porcelain", cwd=derived) == "", "Preview wrote files")
        run(*bootstrap, "--write", cwd=derived)
        expected_paths = {"README.md", "backend/README.md", ".env_examples", "compose.yaml",
                          "compose.test.yaml", "compose.prod.yaml", "backend/app/core/config/settings.py",
                          "frontend/index.html", "frontend/src/shared/i18n/ui-text.ts",
                          "frontend/package.json", "frontend/package-lock.json", "docs/ai/template_provenance.json"}
        changed = set(run("git", "diff", "--name-only", cwd=derived).splitlines())
        changed.update(run("git", "ls-files", "--others", "--exclude-standard", cwd=derived).splitlines())
        require(changed == expected_paths, "Unexpected bootstrap changed-file set")
        provenance_path = derived / "docs/ai/template_provenance.json"
        provenance_bytes = provenance_path.read_bytes()
        provenance = json.loads(provenance_bytes)
        require(provenance["template_commit"] == candidate and provenance["template_tree"] == candidate_tree,
                "Bootstrap origin differs from candidate")
        require(provenance["template_contract_version"] == "foundation-bootstrap-v1", "Bootstrap contract")
        before_repeat = {path: (derived / path).read_bytes() for path in expected_paths}
        result = subprocess.run([*bootstrap, "--write"], cwd=derived, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        require(result.returncode != 0, "Repeated bootstrap accepted")
        require(before_repeat == {path: (derived / path).read_bytes() for path in expected_paths},
                "Refused bootstrap mutated identity")
        run("git", "add", "--", *sorted(expected_paths), cwd=derived)
        run("git", "-c", "user.name=Release Validation", "-c", "user.email=release@example.test",
            "commit", "-m", "test: freeze disposable derived identity", cwd=derived)
        print(f"DERIVED {run('git', 'rev-parse', 'HEAD', cwd=derived)} "
              f"TREE {run('git', 'rev-parse', 'HEAD^{tree}', cwd=derived)} "
              f"PROVENANCE_SHA256 {hashlib.sha256(provenance_bytes).hexdigest()}")
        print("DERIVED_PROVENANCE " + json.dumps(provenance, sort_keys=True))
        run(python, "-m", "pytest", "tests/contracts", "backend/tests/contracts", "-q", cwd=derived)
        print(run(python, "-m", "pytest", "backend/tests", "--cov=app",
                  "--cov-report=term-missing:skip-covered", "--cov-fail-under=100", cwd=derived))
        run(python, "-m", "mypy", "backend", cwd=derived)
        run(python, "-m", "pip", "check", cwd=derived)
        print(run(python, "-m", "pip_audit", "--local", "--progress-spinner", "off", cwd=derived))
        run("npm", "ci", "--prefix", "frontend", cwd=derived)
        npm_policy(derived)
        print(run("npm", "--prefix", "frontend", "run", "check", cwd=derived))
        print(run("npm", "--prefix", "frontend", "run", "test:e2e:ci", cwd=derived))
        print(run("npm", "--prefix", "frontend", "run", "build", cwd=derived))
        run(python, "scripts/validate_project_skills.py", cwd=derived)
        run(python, "scripts/install_project_skills.py", cwd=derived)
        for files in [("compose.yaml",), ("compose.yaml", "compose.override.yaml"),
                      ("compose.test.yaml",), ("compose.yaml", "compose.test.yaml"),
                      ("compose.yaml", "compose.prod.yaml")]:
            args = [part for file in files for part in ("-f", file)]
            run("docker", "compose", "--env-file", ".env_examples", *args, "config", "-q", cwd=derived)
        service_gate(derived, python)
        image_gate(derived)
        require(run("git", "status", "--porcelain", cwd=derived) == "", "Derived gates changed tracked files")
        print("DERIVED fixture gates passed; provenance retained in sanitized job output")
    except BaseException:
        print("Failed derived fixture retained under RUNNER_TEMP for diagnostics; no recovery artifacts deleted")
        raise
    else:
        shutil.rmtree(temp)
    require(run("git", "status", "--porcelain") == "", "Validation changed tracked candidate")
    print("Hosted services and template reuse validation passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--probe"]:
        probe()
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--source-repository", help="Credential-free template repository HTTP(S) URL")
        main(parser.parse_args().source_repository)
