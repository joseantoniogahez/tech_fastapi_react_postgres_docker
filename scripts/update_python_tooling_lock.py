from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = REPOSITORY_ROOT / "python-tooling-lock.json"
SCHEMA_VERSION = 1
GOVERNED_INPUT_PATHS = frozenset(
    {
        "requirements.txt",
        "backend/requirements.txt",
        "backend/tests/requirements.txt",
    }
)
WINDOWS_LOCK_PATH = "pylock.windows-x86_64.toml"
CI_LOCK_PATH = "pylock.ubuntu-x86_64.toml"
GENERATOR = {
    "name": "pip",
    "version": "26.0.1",
    "python": "3.14.6",
    "platform": "windows-x86_64",
}
INSTALLER = {"name": "pip", "version": "26.2.1"}
CI_PLATFORM = "ubuntu-24.04-x86_64"
CI_GENERATOR = "pip==26.0.1"
CI_INSTALLER = "pip==26.2.1"
CI_PASS_PROOF = {
    "clean_install": "pass",
    "pip_check": "pass",
    "pip_audit": "pass",
}
CI_PENDING_PROOF = {check: "pending" for check in CI_PASS_PROOF}


def coordinate_errors(metadata: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version")
    if metadata.get("generator") != GENERATOR:
        errors.append("generator")
    if metadata.get("installer") != INSTALLER:
        errors.append("installer")

    inputs = metadata.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != GOVERNED_INPUT_PATHS:
        errors.append("inputs")

    lock = metadata.get("lock")
    if not isinstance(lock, dict) or lock.get("path") != WINDOWS_LOCK_PATH:
        errors.append("lock.path")

    ci_lock = metadata.get("ci_lock")
    if not isinstance(ci_lock, dict):
        errors.append("ci_lock")
    else:
        expected_ci_coordinates = {
            "path": CI_LOCK_PATH,
            "platform": CI_PLATFORM,
            "generator": CI_GENERATOR,
            "installer": CI_INSTALLER,
        }
        for field, expected in expected_ci_coordinates.items():
            if ci_lock.get(field) != expected:
                errors.append(f"ci_lock.{field}")
    return errors


def sha256(relative_path: str, repository_root: Path = REPOSITORY_ROOT) -> str:
    return hashlib.sha256((repository_root / relative_path).read_bytes()).hexdigest()


def package_count(relative_path: str, repository_root: Path = REPOSITORY_ROOT) -> int:
    lock = tomllib.loads((repository_root / relative_path).read_text(encoding="utf-8"))
    packages = lock["packages"]
    assert isinstance(packages, list)
    return len(packages)


def refreshed(metadata: dict[str, object], repository_root: Path = REPOSITORY_ROOT) -> dict[str, object]:
    inputs = metadata["inputs"]
    assert isinstance(inputs, dict)
    refreshed_inputs = {str(path): sha256(str(path), repository_root) for path in inputs}
    governed_input_changed = any(inputs.get(path) != checksum for path, checksum in refreshed_inputs.items())
    metadata["inputs"] = refreshed_inputs

    ci_lock_checksum_changed = False
    for key in ("lock", "ci_lock"):
        lock = metadata[key]
        assert isinstance(lock, dict)
        path = lock["path"]
        assert isinstance(path, str)
        checksum = sha256(path, repository_root)
        if key == "ci_lock" and lock.get("sha256") != checksum:
            ci_lock_checksum_changed = True
        lock["sha256"] = checksum
        lock["packages"] = package_count(path, repository_root)

    if governed_input_changed or ci_lock_checksum_changed:
        ci_lock = metadata["ci_lock"]
        assert isinstance(ci_lock, dict)
        ci_lock["status"] = "pending"
        ci_lock["proof"] = dict(CI_PENDING_PROOF)
    return metadata


def stale_metadata(original: dict[str, object], expected: dict[str, object]) -> list[str]:
    original_inputs = original["inputs"]
    expected_inputs = expected["inputs"]
    assert isinstance(original_inputs, dict)
    assert isinstance(expected_inputs, dict)
    stale = [
        str(path)
        for path, checksum in expected_inputs.items()
        if original_inputs.get(path) != checksum
    ]
    for key in ("lock", "ci_lock"):
        original_lock = original[key]
        expected_lock = expected[key]
        assert isinstance(original_lock, dict)
        assert isinstance(expected_lock, dict)
        if (
            original_lock.get("sha256") != expected_lock.get("sha256")
            or original_lock.get("packages") != expected_lock.get("packages")
        ):
            stale.append(str(expected_lock["path"]))

    original_ci_lock = original["ci_lock"]
    assert isinstance(original_ci_lock, dict)
    if original_ci_lock.get("status") != "validated":
        stale.append("ci_lock.status")
    if original_ci_lock.get("proof") != CI_PASS_PROOF:
        stale.append("ci_lock.proof")
    return stale


def run(metadata_path: Path = METADATA_PATH, repository_root: Path = REPOSITORY_ROOT, *, write: bool = False) -> int:
    original = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(original, dict):
        print("invalid lock metadata coordinates: root")
        return 1
    structural_errors = coordinate_errors(original)
    if structural_errors:
        print("invalid lock metadata coordinates: " + ", ".join(structural_errors))
        return 1

    expected = refreshed(json.loads(json.dumps(original)), repository_root)
    stale = stale_metadata(original, expected)
    if not stale and not write:
        print("python-tooling-lock.json metadata is current and CI proof is validated")
        return 0

    if not write:
        print("stale or unvalidated metadata: " + ", ".join(stale))
        print(r"run: .\.venv\Scripts\python.exe scripts\update_python_tooling_lock.py --write")
        return 1

    with metadata_path.open("w", encoding="utf-8", newline="\n") as metadata_file:
        metadata_file.write(json.dumps(expected, indent=2) + "\n")
    print("updated lock metadata: " + (", ".join(stale) or "no content changes"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or refresh Python tooling lock metadata.")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    return run(write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
