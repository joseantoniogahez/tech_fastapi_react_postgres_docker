from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from scripts import install_project_skills as installer

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SCRIPT = REPOSITORY_ROOT / "scripts" / "install_project_skills.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_skill(root: Path, name: str, *, marker: str = "source") -> None:
    _write(
        root / "skills" / name / "SKILL.md",
        f"""---
name: {name}
description: Install a deterministic project skill. Use when Codex validates installer behavior.
---

# {name}

Marker: {marker}
""",
    )
    _write(
        root / "skills" / name / "agents" / "openai.yaml",
        f'''interface:
  display_name: "{name.title()}"
  short_description: "Install a deterministic project skill"
  default_prompt: "Use ${name} to validate project skill installation."
''',
    )


def _repository(tmp_path: Path, names: tuple[str, ...] = ("alpha-skill", "beta-skill")) -> Path:
    root = tmp_path / "repository fixture"
    _write(root / "AGENTS.md", "# Agents\n")
    (root / "docs").mkdir(parents=True)
    (root / "scripts").mkdir()
    for name in names:
        _write_skill(root, name)
    return root


def _run(root: Path, destination: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(INSTALLER_SCRIPT),
            "--root",
            str(root),
            "--dest",
            str(destination),
            *arguments,
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


def test_invalid_skill_blocks_discovery_before_selection_or_copy(tmp_path: Path) -> None:
    root = _repository(tmp_path, names=("valid-skill",))
    _write(root / "skills" / "invalid-skill" / "SKILL.md", "# missing frontmatter\n")
    destination = tmp_path / "destination"

    result = _run(root, destination, "--skill", "valid-skill", "--write")

    assert result.returncode == 2
    assert "Project skill pack is invalid" in result.stderr
    assert "invalid-skill" in result.stderr
    assert "would install" not in result.stdout
    assert "installed:" not in result.stdout
    assert not destination.exists()


def test_dry_run_does_not_create_destination(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    destination = tmp_path / "absent destination"

    result = _run(root, destination)

    assert result.returncode == 0, result.stderr
    assert "mode: dry-run" in result.stdout
    assert "would install: alpha-skill" in result.stdout
    assert not destination.exists()


def test_conflict_preserves_existing_target_and_installs_nothing(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    destination = tmp_path / "destination"
    _write(destination / "alpha-skill" / "existing.txt", "keep alpha\n")
    before = _tree_snapshot(destination)

    result = _run(root, destination, "--write")

    assert result.returncode == 2
    assert "require --force: alpha-skill" in result.stderr
    assert _tree_snapshot(destination) == before
    assert not (destination / "beta-skill").exists()


def test_failed_restore_retains_backups_and_restores_independent_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repository(tmp_path, names=("alpha-skill", "beta-skill", "gamma-skill"))
    destination = tmp_path / "destination"
    for name in ("alpha-skill", "beta-skill"):
        _write(destination / name / "existing.txt", f"original {name}\n")
    alpha_before = _tree_snapshot(destination / "alpha-skill")
    beta_before = _tree_snapshot(destination / "beta-skill")
    actions = installer.collect_actions(
        available_skills=installer.discover_project_skills(root / "skills", root),
        requested_skills=None,
        destination_root=destination,
        force=True,
    )
    original_move = installer._move_path

    def fail_commit_and_one_restore(source: Path, target: Path) -> None:
        if (source.parent.name, source.name) in {
            ("stage", "gamma-skill"), ("backup", "beta-skill"),
        }:
            raise OSError("simulated rename failure")
        original_move(source, target)

    monkeypatch.setattr(installer, "_move_path", fail_commit_and_one_restore)
    with pytest.raises(installer.SkillInstallError, match="rollback was incomplete") as failure:
        installer.apply_actions(actions, destination)

    transactions = list(destination.glob(".project-skills-*"))
    assert len(transactions) == 1
    assert _tree_snapshot(transactions[0] / "backup" / "beta-skill") == beta_before
    assert _tree_snapshot(destination / "alpha-skill") == alpha_before
    assert not (destination / "gamma-skill").exists()
    assert str(transactions[0]) in str(failure.value)
    assert str(destination / "beta-skill") in str(failure.value)
    assert "previous destinations restored" not in str(failure.value)


def test_force_replaces_only_the_exact_selected_target(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    destination = tmp_path / "destination"
    _write(destination / "alpha-skill" / "existing.txt", "old alpha\n")
    _write(destination / "beta-skill" / "existing.txt", "old beta\n")
    beta_before = _tree_snapshot(destination / "beta-skill")

    result = _run(root, destination, "--skill", "alpha-skill", "--force", "--write")

    assert result.returncode == 0, result.stderr
    assert installer.directories_match(root / "skills" / "alpha-skill", destination / "alpha-skill")
    assert _tree_snapshot(destination / "beta-skill") == beta_before


def test_temporary_destination_with_spaces_installs_portably(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    destination = tmp_path / "portable destination" / "nested skills"

    result = _run(root, destination, "--write")

    assert result.returncode == 0, result.stderr
    assert installer.directories_match(root / "skills" / "alpha-skill", destination / "alpha-skill")
    assert installer.directories_match(root / "skills" / "beta-skill", destination / "beta-skill")


def test_late_commit_failure_rolls_back_the_entire_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _repository(tmp_path)
    destination = tmp_path / "destination"
    _write(destination / "alpha-skill" / "existing.txt", "old alpha\n")
    before = _tree_snapshot(destination)
    available = installer.discover_project_skills(root / "skills", root)
    actions = installer.collect_actions(
        available_skills=available,
        requested_skills=None,
        destination_root=destination,
        force=True,
    )
    original_move = installer._move_path

    def fail_on_second_staged_skill(source: Path, target: Path) -> None:
        if source.parent.name == "stage" and source.name == "beta-skill":
            raise OSError("simulated late commit failure")
        original_move(source, target)

    monkeypatch.setattr(installer, "_move_path", fail_on_second_staged_skill)

    with pytest.raises(installer.SkillInstallError, match="previous destinations restored"):
        installer.apply_actions(actions, destination)

    assert _tree_snapshot(destination) == before
    assert not (destination / "beta-skill").exists()
