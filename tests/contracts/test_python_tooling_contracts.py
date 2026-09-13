from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from scripts import update_python_tooling_lock

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PIN_PATTERN = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)(?:\[[^]]+\])?==(?P<version>[^\s]+)$")


def _pinned_requirements(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = PIN_PATTERN.fullmatch(raw_line.strip())
        if match:
            pins[match.group("name").lower()] = match.group("version")
    return pins


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_test_lock(path: Path, package_names: tuple[str, ...]) -> None:
    packages = "".join(f'[[packages]]\nname = "{name}"\nversion = "1.0"\n\n' for name in package_names)
    path.write_text(f'lock-version = "1.0"\ncreated-by = "pip"\n\n{packages}', encoding="utf-8")


def _read_metadata(path: Path) -> dict[str, object]:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(metadata, dict)
    return metadata


def _write_metadata(path: Path, metadata: dict[str, object]) -> None:
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def _metadata_section(metadata: dict[str, object], key: str) -> dict[str, object]:
    section = metadata[key]
    assert isinstance(section, dict)
    return section


def _apply_coordinate_drift(metadata: dict[str, object], drift: str) -> None:
    if drift == "schema_version":
        metadata["schema_version"] = 2
    elif drift == "removed_input":
        _metadata_section(metadata, "inputs").pop("backend/tests/requirements.txt")
    elif drift == "extra_input":
        _metadata_section(metadata, "inputs")["untracked-requirements.txt"] = "0" * 64
    elif drift == "windows_lock_path":
        _metadata_section(metadata, "lock")["path"] = "alternate-windows-lock.toml"
    elif drift == "generator":
        metadata["generator"] = {**update_python_tooling_lock.GENERATOR, "version": "unexpected"}
    elif drift == "installer":
        metadata["installer"] = {**update_python_tooling_lock.INSTALLER, "version": "unexpected"}
    elif drift == "ci_lock_path":
        _metadata_section(metadata, "ci_lock")["path"] = "alternate-ci-lock.toml"
    elif drift == "ci_platform":
        _metadata_section(metadata, "ci_lock")["platform"] = "ubuntu-latest"
    elif drift == "ci_generator":
        _metadata_section(metadata, "ci_lock")["generator"] = "pip==unexpected"
    elif drift == "ci_installer":
        _metadata_section(metadata, "ci_lock")["installer"] = "pip==unexpected"
    else:
        raise AssertionError(f"Unhandled coordinate drift fixture: {drift}")


@pytest.fixture
def tooling_lock_fixture(tmp_path: Path) -> tuple[Path, Path]:
    input_paths = tuple(tmp_path / relative_path for relative_path in update_python_tooling_lock.GOVERNED_INPUT_PATHS)
    for input_path in input_paths:
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text("example==1.0\n", encoding="utf-8")
    windows_lock_path = tmp_path / "pylock.windows-x86_64.toml"
    ci_lock_path = tmp_path / "pylock.ubuntu-x86_64.toml"
    _write_test_lock(windows_lock_path, ("example",))
    _write_test_lock(ci_lock_path, ("example",))

    metadata_path = tmp_path / "python-tooling-lock.json"
    metadata: dict[str, object] = {
        "schema_version": 1,
        "generator": {
            "name": "pip",
            "version": "26.0.1",
            "python": "3.14.6",
            "platform": "windows-x86_64",
        },
        "installer": {"name": "pip", "version": "26.2.1"},
        "inputs": {
            input_path.relative_to(tmp_path).as_posix(): _sha256(input_path)
            for input_path in input_paths
        },
        "lock": {
            "path": windows_lock_path.name,
            "sha256": _sha256(windows_lock_path),
            "packages": 1,
        },
        "ci_lock": {
            "path": ci_lock_path.name,
            "platform": "ubuntu-24.04-x86_64",
            "status": "validated",
            "generator": "pip==26.0.1",
            "installer": "pip==26.2.1",
            "sha256": _sha256(ci_lock_path),
            "packages": 1,
            "proof": {
                "clean_install": "pass",
                "pip_check": "pass",
                "pip_audit": "pass",
            },
        },
    }
    _write_metadata(metadata_path, metadata)
    return tmp_path, metadata_path


def test_root_tools_are_explicitly_pinned() -> None:
    assert _pinned_requirements(REPOSITORY_ROOT / "requirements.txt") == {
        "flake8-pyproject": "1.2.4",
        "mypy": "1.20.2",
        "pip": "26.2.1",
        "pip-audit": "2.10.1",
        "pre-commit": "4.6.0",
    }


def test_mypy_hook_matches_backend_and_test_manifests() -> None:
    config = yaml.safe_load((REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    mypy_repository = next(repo for repo in config["repos"] if repo["repo"].endswith("mirrors-mypy"))
    mypy_hook = next(hook for hook in mypy_repository["hooks"] if hook["id"] == "mypy")
    hook_pins: dict[str, str] = {}
    for requirement in mypy_hook["additional_dependencies"]:
        match = PIN_PATTERN.fullmatch(requirement)
        assert match is not None, requirement
        hook_pins[match.group("name").lower()] = match.group("version")

    manifest_pins = _pinned_requirements(REPOSITORY_ROOT / "backend" / "requirements.txt")
    manifest_pins.update(_pinned_requirements(REPOSITORY_ROOT / "backend" / "tests" / "requirements.txt"))
    assert mypy_repository["rev"] == "v1.20.2"
    assert hook_pins == manifest_pins


def test_python_tooling_lock_hook_checks_all_governed_files() -> None:
    config = yaml.safe_load((REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    local_repository = next(repo for repo in config["repos"] if repo["repo"] == "local")
    hook = next(hook for hook in local_repository["hooks"] if hook["id"] == "python-tooling-lock-check")

    assert hook["entry"] == "python scripts/update_python_tooling_lock.py"
    assert hook["language"] == "python"
    assert hook["pass_filenames"] is False
    pattern = re.compile(hook["files"])
    governed_paths = {
        "requirements.txt",
        "backend/requirements.txt",
        "backend/tests/requirements.txt",
        "pylock.windows-x86_64.toml",
        "pylock.ubuntu-x86_64.toml",
        "python-tooling-lock.json",
        "scripts/update_python_tooling_lock.py",
    }
    assert all(pattern.fullmatch(path) for path in governed_paths)


def _assert_lock_has_versions_and_sha256_artifacts(path: Path, expected_packages: int) -> None:
    lock = tomllib.loads(path.read_text(encoding="utf-8"))
    assert lock["lock-version"] == "1.0"
    assert lock["created-by"] == "pip"
    assert len(lock["packages"]) == expected_packages

    package_names = {package["name"] for package in lock["packages"]}
    assert "httpx2" in package_names
    assert "httpx" not in package_names

    for package in lock["packages"]:
        assert package["version"]
        assert package["wheels"]
        for wheel in package["wheels"]:
            assert re.fullmatch(r"[0-9a-f]{64}", wheel["hashes"]["sha256"])


def test_platform_locks_have_versions_and_sha256_artifacts() -> None:
    metadata = json.loads((REPOSITORY_ROOT / "python-tooling-lock.json").read_text(encoding="utf-8"))
    _assert_lock_has_versions_and_sha256_artifacts(
        REPOSITORY_ROOT / metadata["lock"]["path"], metadata["lock"]["packages"]
    )
    _assert_lock_has_versions_and_sha256_artifacts(
        REPOSITORY_ROOT / metadata["ci_lock"]["path"], metadata["ci_lock"]["packages"]
    )


def test_lock_metadata_checksums_match_governed_inputs() -> None:
    metadata = json.loads((REPOSITORY_ROOT / "python-tooling-lock.json").read_text(encoding="utf-8"))
    assert metadata["generator"] == {
        "name": "pip",
        "version": "26.0.1",
        "python": "3.14.6",
        "platform": "windows-x86_64",
    }
    assert metadata["installer"] == {"name": "pip", "version": "26.2.1"}
    for relative_path, expected_hash in metadata["inputs"].items():
        assert _sha256(REPOSITORY_ROOT / relative_path) == expected_hash
    assert _sha256(REPOSITORY_ROOT / metadata["lock"]["path"]) == metadata["lock"]["sha256"]
    assert metadata["ci_lock"]["status"] == "validated"
    assert metadata["ci_lock"]["platform"] == "ubuntu-24.04-x86_64"
    assert metadata["ci_lock"]["proof"] == {
        "clean_install": "pass",
        "pip_check": "pass",
        "pip_audit": "pass",
    }
    assert _sha256(REPOSITORY_ROOT / metadata["ci_lock"]["path"]) == metadata["ci_lock"]["sha256"]


def test_current_lock_metadata_passes_the_read_only_guard() -> None:
    metadata_path = REPOSITORY_ROOT / "python-tooling-lock.json"
    original = metadata_path.read_bytes()

    assert update_python_tooling_lock.run(metadata_path, REPOSITORY_ROOT) == 0
    assert metadata_path.read_bytes() == original


@pytest.mark.parametrize(
    "drift",
    (
        "schema_version",
        "removed_input",
        "extra_input",
        "windows_lock_path",
        "generator",
        "installer",
        "ci_lock_path",
        "ci_platform",
        "ci_generator",
        "ci_installer",
    ),
)
def test_structural_coordinate_drift_is_rejected_before_refresh_in_all_modes(
    tooling_lock_fixture: tuple[Path, Path], drift: str
) -> None:
    repository_root, metadata_path = tooling_lock_fixture
    metadata = _read_metadata(metadata_path)
    _apply_coordinate_drift(metadata, drift)
    _write_metadata(metadata_path, metadata)
    drifted = metadata_path.read_bytes()

    assert update_python_tooling_lock.run(metadata_path, repository_root) == 1
    assert update_python_tooling_lock.run(metadata_path, repository_root, write=True) == 1
    assert metadata_path.read_bytes() == drifted


@pytest.mark.parametrize("lock_key", ("lock", "ci_lock"))
def test_read_only_guard_rejects_stale_package_counts(
    tooling_lock_fixture: tuple[Path, Path], lock_key: str
) -> None:
    repository_root, metadata_path = tooling_lock_fixture
    metadata = _read_metadata(metadata_path)
    _metadata_section(metadata, lock_key)["packages"] = 2
    _write_metadata(metadata_path, metadata)

    assert update_python_tooling_lock.run(metadata_path, repository_root) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("status", "pending"),
        (
            "proof",
            {
                "clean_install": "pass",
                "pip_check": "pass",
                "pip_audit": "pass",
                "unrecognized_check": "pass",
            },
        ),
    ),
)
def test_read_only_guard_requires_validated_ci_status_and_exact_pass_proof(
    tooling_lock_fixture: tuple[Path, Path], field: str, value: object
) -> None:
    repository_root, metadata_path = tooling_lock_fixture
    metadata = _read_metadata(metadata_path)
    _metadata_section(metadata, "ci_lock")[field] = value
    _write_metadata(metadata_path, metadata)

    assert update_python_tooling_lock.run(metadata_path, repository_root) == 1


def test_write_invalidates_ci_proof_when_a_governed_input_changes(
    tooling_lock_fixture: tuple[Path, Path],
) -> None:
    repository_root, metadata_path = tooling_lock_fixture
    input_path = repository_root / "requirements.txt"
    input_path.write_text("example==2.0\n", encoding="utf-8")

    assert update_python_tooling_lock.run(metadata_path, repository_root, write=True) == 0

    updated = _read_metadata(metadata_path)
    assert _metadata_section(updated, "inputs")["requirements.txt"] == _sha256(input_path)
    assert _metadata_section(updated, "ci_lock")["status"] == "pending"
    assert _metadata_section(updated, "ci_lock")["proof"] == {
        "clean_install": "pending",
        "pip_check": "pending",
        "pip_audit": "pending",
    }
    assert update_python_tooling_lock.run(metadata_path, repository_root) == 1


def test_write_invalidates_ci_proof_when_the_ci_lock_changes(
    tooling_lock_fixture: tuple[Path, Path],
) -> None:
    repository_root, metadata_path = tooling_lock_fixture
    ci_lock_path = repository_root / "pylock.ubuntu-x86_64.toml"
    _write_test_lock(ci_lock_path, ("example", "second"))

    assert update_python_tooling_lock.run(metadata_path, repository_root, write=True) == 0

    updated = _read_metadata(metadata_path)
    ci_lock = _metadata_section(updated, "ci_lock")
    assert ci_lock["sha256"] == _sha256(ci_lock_path)
    assert ci_lock["packages"] == 2
    assert ci_lock["status"] == "pending"
    assert ci_lock["proof"] == {
        "clean_install": "pending",
        "pip_check": "pending",
        "pip_audit": "pending",
    }
    assert update_python_tooling_lock.run(metadata_path, repository_root) == 1


def test_write_preserves_ci_proof_for_a_windows_lock_only_change(
    tooling_lock_fixture: tuple[Path, Path],
) -> None:
    repository_root, metadata_path = tooling_lock_fixture
    windows_lock_path = repository_root / "pylock.windows-x86_64.toml"
    _write_test_lock(windows_lock_path, ("example", "second"))

    assert update_python_tooling_lock.run(metadata_path, repository_root, write=True) == 0

    updated = _read_metadata(metadata_path)
    windows_lock = _metadata_section(updated, "lock")
    ci_lock = _metadata_section(updated, "ci_lock")
    assert windows_lock["sha256"] == _sha256(windows_lock_path)
    assert windows_lock["packages"] == 2
    assert ci_lock["status"] == "validated"
    assert ci_lock["proof"] == {
        "clean_install": "pass",
        "pip_check": "pass",
        "pip_audit": "pass",
    }
    assert update_python_tooling_lock.run(metadata_path, repository_root) == 0


def test_optional_reference_capabilities_stay_out_of_core() -> None:
    direct_pins = _pinned_requirements(REPOSITORY_ROOT / "requirements.txt")
    direct_pins.update(_pinned_requirements(REPOSITORY_ROOT / "backend" / "requirements.txt"))
    excluded = {"anthropic", "boto3", "cryptography", "openai", "pypdf", "rq"}
    assert direct_pins.keys().isdisjoint(excluded)


def test_installation_docs_have_no_floating_pip_upgrade() -> None:
    governed_docs = (
        REPOSITORY_ROOT / "README.md",
        REPOSITORY_ROOT / "backend" / "README.md",
        REPOSITORY_ROOT / "docs" / "ai" / "python_tooling.md",
    )
    for path in governed_docs:
        content = path.read_text(encoding="utf-8").lower()
        assert "pip install --upgrade pip" not in content
        assert "pip install -u pip" not in content


def test_windows_installation_docs_verify_tooling_lock_before_consuming_it() -> None:
    governed_docs = (
        REPOSITORY_ROOT / "README.md",
        REPOSITORY_ROOT / "backend" / "README.md",
        REPOSITORY_ROOT / "docs" / "ai" / "python_tooling.md",
    )
    verifier = r".\.venv\Scripts\python.exe scripts\update_python_tooling_lock.py"
    installer = (
        r".\.venv\Scripts\python.exe -m pip install --requirement "
        r"pylock.windows-x86_64.toml"
    )

    for path in governed_docs:
        content = path.read_text(encoding="utf-8")
        assert verifier in content, path
        assert installer in content, path
        assert content.index(verifier) < content.index(installer), path
