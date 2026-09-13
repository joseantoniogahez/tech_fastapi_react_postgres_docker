from __future__ import annotations

import json
import re
from pathlib import Path

import yaml  # type: ignore[import-untyped]

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yaml"
TRUSTED_CACHE_CONDITION = (
    "github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository"
)
LOCK_VERIFICATION_NAME = "Verify Python tooling lock metadata, checksums, and proof"
LOCK_VERIFICATION_COMMAND = "python scripts/update_python_tooling_lock.py"
ACTION_PINS = {
    "actions/checkout": ("3d3c42e5aac5ba805825da76410c181273ba90b1", "v7.0.1"),  # pragma: allowlist secret
    "actions/setup-python": ("5fda3b95a4ea91299a34e894583c3862153e4b97", "v7.0.0"),  # pragma: allowlist secret
    "actions/setup-node": ("820762786026740c76f36085b0efc47a31fe5020", "v7.0.0"),  # pragma: allowlist secret
    "actions/cache": ("55cc8345863c7cc4c66a329aec7e433d2d1c52a9", "v6.1.0"),  # pragma: allowlist secret
    "docker/setup-docker-action": ("77e84dbf09b47d1e29270283c22f16145aa85ca1", "v5.4.0"),  # pragma: allowlist secret
    "docker/setup-compose-action": ("4eb059ff7f16592f9c84d5ca339c53cb7c5064e2", "v2.3.0"),  # pragma: allowlist secret
}


def _workflow() -> tuple[dict[str, object], str]:
    raw = WORKFLOW_PATH.read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed, raw


def _steps(workflow: dict[str, object]) -> list[dict[str, object]]:
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    result: list[dict[str, object]] = []
    for job in jobs.values():
        assert isinstance(job, dict)
        steps = job["steps"]
        assert isinstance(steps, list)
        result.extend(step for step in steps if isinstance(step, dict))
    return result


def test_ci_has_minimum_permissions_and_no_secret_bearing_trigger() -> None:
    workflow, raw = _workflow()

    assert workflow["permissions"] == {"contents": "read"}
    assert "pull_request_target" not in raw
    assert "secrets." not in raw
    assert "write-all" not in raw
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    assert all("permissions" not in job for job in jobs.values() if isinstance(job, dict))


def test_every_external_action_uses_the_verified_immutable_sha() -> None:
    _, raw = _workflow()
    matches = re.findall(r"^\s*uses:\s*([^@\s]+)@([0-9a-f]{40})\s+#\s+(v\S+)\s*$", raw, re.MULTILINE)
    assert matches
    seen: set[str] = set()
    for action, sha, version in matches:
        assert ACTION_PINS[action] == (sha, version)
        seen.add(action)
    assert seen == ACTION_PINS.keys()
    assert len(matches) == raw.count("uses:")


def test_ci_uses_the_accepted_exact_runner_matrix_and_locked_installs() -> None:
    workflow, raw = _workflow()
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    assert all(job["runs-on"] == "ubuntu-24.04" for job in jobs.values() if isinstance(job, dict))

    assert 'python-version: "3.14.6"' in raw
    assert "python -m pip install pip==26.2.1" in raw
    assert 'node-version: "22.23.1"' in raw
    assert "npm install --global npm@12.0.1" in raw
    assert 'test "$(npm --version)" = "12.0.1"' in raw
    assert "python -m pip install --requirement pylock.ubuntu-x86_64.toml" in raw
    assert "npm ci --prefix frontend" in raw
    assert "pip install --upgrade" not in raw
    assert "pip install -r requirements.txt" not in raw
    assert "runs-on: ubuntu-latest" not in raw
    assert "version: v29.6.2" in raw
    assert "version: v5.3.1" in raw
    assert "{{.Client.Version}}" in raw
    assert "{{.Server.Version}}" in raw

    metadata = (REPOSITORY_ROOT / "python-tooling-lock.json").read_text(encoding="utf-8")
    assert '"status": "validated"' in metadata
    assert (REPOSITORY_ROOT / "pylock.ubuntu-x86_64.toml").is_file()


def test_frontend_package_metadata_matches_the_node_and_npm_contract() -> None:
    package = json.loads((REPOSITORY_ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    package_lock = json.loads(
        (REPOSITORY_ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8")
    )

    expected_engines = {
        "node": ">=22.22.2 <23.0.0",
        "npm": ">=12.0.0 <12.1.0",
    }
    assert package["packageManager"] == "npm@12.0.1"
    assert package["engines"] == expected_engines
    assert package["allowScripts"] == {"esbuild@0.27.3": True}
    assert package_lock["packages"][""]["engines"] == expected_engines
    scripted_non_optional_packages = {
        path: metadata["version"]
        for path, metadata in package_lock["packages"].items()
        if metadata.get("hasInstallScript") and not metadata.get("optional")
    }
    assert scripted_non_optional_packages == {"node_modules/esbuild": "0.27.3"}
    assert (REPOSITORY_ROOT / "frontend" / ".npmrc").read_text(encoding="utf-8") == (
        "strict-allow-scripts=true\n"
    )


def test_each_job_verifies_python_tooling_lock_before_caches_and_locked_installs() -> None:
    workflow, _ = _workflow()
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    assert set(jobs) == {"governance", "backend", "frontend"}

    locked_install_commands = (
        "python -m pip install --requirement pylock.ubuntu-x86_64.toml",
        "npm ci --prefix frontend",
    )
    for job in jobs.values():
        assert isinstance(job, dict)
        steps = job["steps"]
        assert isinstance(steps, list)

        setup_python_indices = [
            index
            for index, step in enumerate(steps)
            if isinstance(step, dict) and str(step.get("uses", "")).startswith("actions/setup-python@")
        ]
        verification_indices = [
            index
            for index, step in enumerate(steps)
            if isinstance(step, dict) and step.get("run") == LOCK_VERIFICATION_COMMAND
        ]
        assert len(setup_python_indices) == 1
        assert len(verification_indices) == 1

        verification_index = verification_indices[0]
        verification_step = steps[verification_index]
        assert isinstance(verification_step, dict)
        assert verification_step == {
            "name": LOCK_VERIFICATION_NAME,
            "run": LOCK_VERIFICATION_COMMAND,
        }

        cache_or_install_indices = [
            index
            for index, step in enumerate(steps)
            if isinstance(step, dict)
            and (
                str(step.get("uses", "")).startswith("actions/cache@")
                or any(command in str(step.get("run", "")) for command in locked_install_commands)
            )
        ]
        assert cache_or_install_indices
        assert setup_python_indices[0] < verification_index
        assert all(verification_index < index for index in cache_or_install_indices)


def test_container_runtime_coordinates_match_the_accepted_matrix() -> None:
    backend_dockerfile = (REPOSITORY_ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
    frontend_dockerfile = (REPOSITORY_ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    compose_base = (REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8")
    compose_test = (REPOSITORY_ROOT / "compose.test.yaml").read_text(encoding="utf-8")
    env_example = (REPOSITORY_ROOT / ".env_examples").read_text(encoding="utf-8")

    assert backend_dockerfile.startswith("ARG PYTHON_VERSION=3.14.6\nFROM python:${PYTHON_VERSION}-slim")
    assert frontend_dockerfile.startswith("FROM node:22.23.1-alpine AS base")
    assert "npm install -g npm@12.0.1" in frontend_dockerfile
    assert "COPY package.json package-lock.json .npmrc ./" in frontend_dockerfile
    assert 'PYTHON_VERSION: "${PYTHON_VERSION:-3.14.6}"' in compose_base
    assert "python:${PYTHON_VERSION:-3.14.6}-slim" in compose_test
    assert "node:22.23.1-alpine" in compose_test
    assert "npm install -g npm@12.0.1" in compose_test
    assert "PYTHON_VERSION=3.14.6" in env_example


def test_checkout_and_caches_are_fork_safe_and_content_addressed() -> None:
    workflow, _ = _workflow()
    steps = _steps(workflow)

    checkouts = [step for step in steps if str(step.get("uses", "")).startswith("actions/checkout@")]
    assert checkouts
    assert all(step.get("with") == {"persist-credentials": False} for step in checkouts)

    setup_nodes = [step for step in steps if str(step.get("uses", "")).startswith("actions/setup-node@")]
    assert setup_nodes
    expected_node_inputs = {
        "node-version": "22.23.1",
        "architecture": "x64",
        "check-latest": False,
        "package-manager-cache": False,
    }
    assert all(step.get("with") == expected_node_inputs for step in setup_nodes)

    setup_pythons = [step for step in steps if str(step.get("uses", "")).startswith("actions/setup-python@")]
    expected_python_inputs = {
        "python-version": "3.14.6",
        "architecture": "x64",
        "check-latest": False,
    }
    assert setup_pythons
    assert all(step.get("with") == expected_python_inputs for step in setup_pythons)

    setup_docker = next(step for step in steps if str(step.get("uses", "")).startswith("docker/setup-docker-action@"))
    assert setup_docker.get("with") == {"version": "v29.6.2"}
    setup_compose = next(step for step in steps if str(step.get("uses", "")).startswith("docker/setup-compose-action@"))
    assert setup_compose.get("with") == {"version": "v5.3.1", "cache-binary": False}

    cache_steps = [step for step in steps if str(step.get("uses", "")).startswith("actions/cache@")]
    assert cache_steps
    for step in cache_steps:
        assert step.get("if") == TRUSTED_CACHE_CONDITION
        inputs = step.get("with")
        assert isinstance(inputs, dict)
        key = str(inputs["key"])
        assert "runner.os" in key
        assert "hashFiles(" in key
        assert "restore-keys" not in inputs


def test_ci_runs_governance_docs_audits_headers_and_valid_playwright_command() -> None:
    workflow, raw = _workflow()
    required = (
        "python scripts/validate_project_skills.py --root .",
        "python -m pytest tests/contracts backend/tests/contracts",
        "python -m pip check",
        "python -m pip_audit --local --progress-spinner off",
        "python -m mypy backend",
        "npm --prefix frontend run deps:audit",
        "npm --prefix frontend run check",
        "npm --prefix frontend run test:e2e:ci",
        "npm --prefix frontend run build",
        "node frontend/scripts/security-headers-smoke.mjs",
        "python -m pre_commit run --all-files --hook-stage pre-commit",
        "python -m pre_commit run --all-files --hook-stage pre-push",
        "npm --prefix frontend exec -- playwright install --with-deps chromium",
    )
    for command in required:
        assert command in raw
    assert "npm --prefix frontend exec playwright" not in raw
    assert "for attempt in {1..15}" in raw
    assert "docker logs frontend-security-smoke" in raw

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    frontend = jobs["frontend"]
    assert isinstance(frontend, dict)
    quality_step = next(step for step in frontend["steps"] if step.get("name") == "Run frontend quality gate")
    assert quality_step["env"] == {"OPENAPI_PYTHON": "python"}


def test_precommit_validates_all_five_compose_forms_without_direct_ci_duplicates() -> None:
    _, raw = _workflow()
    precommit_raw = (REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    commands = (
        "docker compose --env-file .env_examples -f compose.yaml config -q",
        "docker compose --env-file .env_examples -f compose.yaml -f compose.override.yaml config -q",
        "docker compose --env-file .env_examples -f compose.test.yaml config -q",
        "docker compose --env-file .env_examples -f compose.yaml -f compose.test.yaml config -q",
        "docker compose --env-file .env_examples -f compose.yaml -f compose.prod.yaml config -q",
    )
    assert all(command not in raw for command in commands)
    assert all(precommit_raw.count(command) == 1 for command in commands)


def test_precommit_stages_are_disjoint() -> None:
    precommit = yaml.safe_load((REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    assert precommit["default_stages"] == ["pre-commit"]

    pre_push_hook_ids = {
        hook["id"]
        for repository in precommit["repos"]
        for hook in repository["hooks"]
        if hook.get("stages") == ["pre-push"]
    }
    assert pre_push_hook_ids == {"frontend-typecheck", "bandit", "mypy"}


def test_markdownlint_uses_the_locked_system_npm_under_npm_12() -> None:
    precommit = yaml.safe_load((REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    frontend_package = json.loads((REPOSITORY_ROOT / "frontend" / "package.json").read_text(encoding="utf-8"))
    frontend_lock = json.loads((REPOSITORY_ROOT / "frontend" / "package-lock.json").read_text(encoding="utf-8"))

    local_repository = next(repository for repository in precommit["repos"] if repository["repo"] == "local")
    markdownlint = next(hook for hook in local_repository["hooks"] if hook["id"] == "markdownlint")

    assert markdownlint["language"] == "system"
    assert markdownlint["entry"] == "npm --prefix frontend exec --offline -- markdownlint"
    assert markdownlint["args"] == ["--disable", "MD013", "--"]
    assert frontend_package["devDependencies"]["markdownlint-cli"] == "0.48.0"
    assert frontend_lock["packages"][""]["devDependencies"]["markdownlint-cli"] == "0.48.0"
    assert frontend_lock["packages"]["node_modules/markdownlint-cli"]["version"] == "0.48.0"
    assert all(
        repository["repo"] != "https://github.com/igorshubovych/markdownlint-cli"
        for repository in precommit["repos"]
    )


def test_compose_test_commands_have_exact_bootstraps_and_precommit_checks_both_forms() -> None:
    compose_test = (REPOSITORY_ROOT / "compose.test.yaml").read_text(encoding="utf-8")
    precommit = yaml.safe_load((REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    local_repository = next(repo for repo in precommit["repos"] if repo["repo"] == "local")
    entries = {hook["id"]: hook["entry"] for hook in local_repository["hooks"]}

    assert "python -m pip install pip==26.2.1" in compose_test
    assert "python -m pytest tests" in compose_test
    assert "pip install --upgrade" not in compose_test
    assert "npm install -g npm@12.0.1 && npm ci && npm test" in compose_test
    env_prefix = "docker compose --env-file .env_examples"
    assert entries["compose-test-standalone-config"] == f"{env_prefix} -f compose.test.yaml config -q"
    assert entries["compose-test-config"] == f"{env_prefix} -f compose.yaml -f compose.test.yaml config -q"
    assert all(entry.startswith(env_prefix) for hook_id, entry in entries.items() if hook_id.startswith("compose-"))
