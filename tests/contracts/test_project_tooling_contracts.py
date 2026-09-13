from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.validate_project_skills import main as validator_main

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GLOBAL_PYTHON_COMMAND = re.compile(
    r"(?<![\w./\\-])(?:python(?:3(?:\.\d+)*)?(?:\.exe)?|"
    r"pytest(?=\s+(?:-|backend(?:[/\\]|\s|$)|tests(?:[/\\]|\s|$)))|"
    r"pre-commit(?=\s+(?:run|install|autoupdate|try-repo))|"
    r"mypy(?=\s+(?:-|backend|scripts))|pip-audit(?=\s+-))\s+"
)


def _governed_command_docs() -> list[Path]:
    fixed = [
        REPOSITORY_ROOT / "AGENTS.md",
        REPOSITORY_ROOT / "README.md",
        REPOSITORY_ROOT / "backend" / "README.md",
        REPOSITORY_ROOT / "frontend" / "README.md",
        REPOSITORY_ROOT / "docs" / "ai" / "README.md",
        REPOSITORY_ROOT / "docs" / "ai" / "backlog_tracking.md",
        REPOSITORY_ROOT / "docs" / "ai" / "new_app_bootstrap_checklist.md",
        REPOSITORY_ROOT / "docs" / "ai" / "python_tooling.md",
        REPOSITORY_ROOT / "docs" / "ai" / "start_new_project.md",
    ]
    expanded = [
        *REPOSITORY_ROOT.glob("backend/docs/**/*.md"),
        *REPOSITORY_ROOT.glob("frontend/docs/**/*.md"),
        *REPOSITORY_ROOT.glob("docs/ai/templates/*.md"),
        *REPOSITORY_ROOT.glob("skills/**/*.md"),
    ]
    return sorted({*fixed, *expanded})


def test_governed_docs_have_no_global_python_tool_commands() -> None:
    violations: list[str] = []
    for path in _governed_command_docs():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            candidate = line.replace(".venv\\Scripts\\python.exe", "governed-python")
            candidate = candidate.replace("./.venv/bin/python", "governed-python")
            candidate = re.sub(
                r"governed-python\s+-m\s+(?:pytest|pre_commit|mypy|pip_audit|pip|flake8|uvicorn|alembic)\b",
                "governed-tool",
                candidate,
            )
            match = GLOBAL_PYTHON_COMMAND.search(candidate)
            if match is None:
                continue
            command = candidate[match.start() :].strip("` ")
            if re.fullmatch(r"(?:py -3\.14|python3\.14) -m venv \.venv", command):
                continue
            violations.append(f"{path.relative_to(REPOSITORY_ROOT).as_posix()}:{line_number}: {line.strip()}")

    assert violations == []


def test_new_app_bootstrapper_uses_executable_root_venv_paths() -> None:
    skill = (REPOSITORY_ROOT / "skills" / "new-app-bootstrapper" / "SKILL.md").read_text(encoding="utf-8")

    assert r"\.\.venv\Scripts\python.exe" not in skill
    assert ".\\.venv\\Scripts\\python.exe" in skill
    assert "./.venv/bin/python" in skill


def test_generated_bootstrap_provenance_is_excluded_from_secret_scanning() -> None:
    provenance_path = "docs/ai/template_provenance.json"
    config = yaml.safe_load((REPOSITORY_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    detect_secrets_repo = next(repo for repo in config["repos"] if repo["repo"].endswith("/detect-secrets"))
    hook = next(hook for hook in detect_secrets_repo["hooks"] if hook["id"] == "detect-secrets")

    assert re.fullmatch(hook["exclude"], provenance_path)

    baseline = json.loads((REPOSITORY_ROOT / ".secrets.baseline").read_text(encoding="utf-8"))
    exclusion_patterns = [
        pattern
        for filter_config in baseline["filters_used"]
        if filter_config["path"] == "detect_secrets.filters.regex.should_exclude_file"
        for pattern in filter_config["pattern"]
    ]
    assert any(re.fullmatch(pattern, provenance_path) for pattern in exclusion_patterns)


def test_validator_cli_uses_stable_exit_codes(tmp_path: Path) -> None:
    assert validator_main(["--root", str(tmp_path / "missing")]) == 2
    assert validator_main(["--root", str(REPOSITORY_ROOT)]) == 0


def test_scaffold_canonical_dry_runs_do_not_write(tmp_path: Path) -> None:
    (tmp_path / "backend").mkdir()
    (tmp_path / "frontend").mkdir()
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    script = REPOSITORY_ROOT / "scripts" / "scaffold_feature.py"

    cases = (
        ("backend", "governance-backend"),
        ("frontend", "governance-frontend"),
        ("full-stack", "governance-full-stack"),
    )
    for command, name in cases:
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(tmp_path), "--dry-run", command, name],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()) == [
        "AGENTS.md"
    ]


def test_scaffold_collision_fails_before_any_write(tmp_path: Path) -> None:
    (tmp_path / "backend" / "app" / "features" / "collision").mkdir(parents=True)
    (tmp_path / "frontend").mkdir()
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    collision = tmp_path / "backend" / "app" / "features" / "collision" / "router.py"
    collision.write_text("existing\n", encoding="utf-8")
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    result = subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts" / "scaffold_feature.py"),
            "--root",
            str(tmp_path),
            "full-stack",
            "collision",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Refusing to overwrite" in result.stderr
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()) == before


def test_scaffold_invalid_name_fails_before_any_write(tmp_path: Path) -> None:
    (tmp_path / "backend").mkdir()
    (tmp_path / "frontend").mkdir()
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts" / "scaffold_feature.py"),
            "--root",
            str(tmp_path),
            "backend",
            "../invalid",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Feature name must" in result.stderr
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()) == [
        "AGENTS.md"
    ]


def test_scaffold_checklists_use_root_venv_commands(tmp_path: Path) -> None:
    (tmp_path / "backend").mkdir()
    (tmp_path / "frontend").mkdir()
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts" / "scaffold_feature.py"),
            "--root",
            str(tmp_path),
            "full-stack",
            "venv-contract",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    checklists = list(tmp_path.rglob("SCAFFOLD_CHECKLIST.md")) + list(
        (tmp_path / "docs" / "ai" / "scaffolds").glob("*_full_stack_checklist.md")
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in checklists)
    assert ".\\.venv\\Scripts\\python.exe -m pytest" in combined
    assert "./.venv/bin/python -m pytest" in combined
    assert "-m pre_commit run --all-files" in combined
    assert "`python -m pytest" not in combined
    assert "`pre-commit run" not in combined
