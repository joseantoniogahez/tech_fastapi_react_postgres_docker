#!/usr/bin/env python3
"""Install repository-local skills into the active Codex skills directory.

Dry-run is the default. Pass --write to copy files.
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validate_project_skills import ValidationIssue, validate_skill

SKILL_NAME_PATTERN = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"


class SkillInstallError(ValueError):
    """Raised when skill install input or filesystem state is invalid."""


@dataclass(frozen=True)
class SkillAction:
    name: str
    source: Path
    target: Path
    action: str


def ensure_repo_root(root: Path) -> Path:
    resolved = root.resolve()
    required = ["AGENTS.md", "skills", "docs", "scripts"]
    missing = [item for item in required if not (resolved / item).exists()]
    if missing:
        raise SkillInstallError(f"Root does not look like this repository. Missing: {', '.join(missing)}")
    return resolved


def default_skills_dest() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def _format_validation_issues(issues: list[ValidationIssue]) -> str:
    return "\n".join(f"- {issue}" for issue in sorted(issues))


def discover_project_skills(skills_root: Path, repository_root: Path) -> dict[str, Path]:
    skill_dirs = sorted(child for child in skills_root.iterdir() if child.is_dir())
    if not skill_dirs:
        raise SkillInstallError(f"No skills found in {skills_root}")

    issues = [issue for skill_dir in skill_dirs for issue in validate_skill(skill_dir, repository_root)]
    if issues:
        raise SkillInstallError(f"Project skill pack is invalid:\n{_format_validation_issues(issues)}")

    return {skill_dir.name: skill_dir for skill_dir in skill_dirs}


def normalize_requested_skills(raw_skills: list[str] | None) -> list[str] | None:
    if not raw_skills:
        return None

    requested: list[str] = []
    seen: set[str] = set()
    for raw_value in raw_skills:
        for item in raw_value.split(","):
            skill_name = item.strip()
            if not skill_name:
                continue
            if not _is_valid_skill_name(skill_name):
                raise SkillInstallError(
                    f"Invalid skill name '{skill_name}'. Use lowercase letters, digits, and hyphens."
                )
            if skill_name not in seen:
                requested.append(skill_name)
                seen.add(skill_name)
    return requested


def _is_valid_skill_name(value: str) -> bool:
    import re

    return re.fullmatch(SKILL_NAME_PATTERN, value) is not None and "--" not in value


def directories_match(source: Path, target: Path) -> bool:
    comparison = filecmp.dircmp(source, target)
    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return False
    for common_file in comparison.common_files:
        if not filecmp.cmp(source / common_file, target / common_file, shallow=False):
            return False
    return all(
        directories_match(source / common_dir, target / common_dir) for common_dir in comparison.common_dirs
    )


def collect_actions(
    *,
    available_skills: dict[str, Path],
    requested_skills: list[str] | None,
    destination_root: Path,
    force: bool,
) -> list[SkillAction]:
    selected_names = requested_skills or sorted(available_skills)
    unknown = [name for name in selected_names if name not in available_skills]
    if unknown:
        known = ", ".join(sorted(available_skills))
        raise SkillInstallError(f"Unknown skill(s): {', '.join(unknown)}. Available skills: {known}")

    actions: list[SkillAction] = []
    for skill_name in selected_names:
        source = available_skills[skill_name]
        target = destination_root / skill_name

        if not target.exists():
            action = "install"
        elif target.is_dir() and directories_match(source, target):
            action = "skip-identical"
        elif force:
            action = "overwrite"
        else:
            action = "conflict"

        actions.append(SkillAction(name=skill_name, source=source, target=target, action=action))
    return actions


def assert_target_within_destination(target: Path, destination_root: Path) -> None:
    resolved_target = target.resolve()
    resolved_destination = destination_root.resolve()
    if resolved_target == resolved_destination:
        raise SkillInstallError(f"Refusing to overwrite destination root: {resolved_destination}")
    if not resolved_target.is_relative_to(resolved_destination):
        raise SkillInstallError(f"Refusing to write outside destination root: {resolved_target}")


def _move_path(source: Path, target: Path) -> None:
    """Atomically rename a staged or existing skill on the destination filesystem."""

    source.replace(target)


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def apply_actions(actions: list[SkillAction], destination_root: Path) -> None:
    conflicts = [action for action in actions if action.action == "conflict"]
    if conflicts:
        names = ", ".join(action.name for action in conflicts)
        raise SkillInstallError(f"Existing non-matching skill(s) require --force: {names}")

    write_actions = [action for action in actions if action.action in {"install", "overwrite"}]
    if not write_actions:
        return
    if destination_root.exists() and not destination_root.is_dir():
        raise SkillInstallError(f"Destination is not a directory: {destination_root}")

    for action in write_actions:
        assert_target_within_destination(action.target, destination_root)

    destination_existed = destination_root.exists()
    destination_parent = destination_root.resolve().parent
    destination_parent.mkdir(parents=True, exist_ok=True)
    transaction_parent = destination_root if destination_existed else destination_parent
    transaction_root = Path(tempfile.mkdtemp(prefix=".project-skills-", dir=transaction_parent))
    stage_root = transaction_root / "stage"
    backup_root = transaction_root / "backup"
    mutations: list[tuple[Path, Path | None]] = []

    try:
        stage_root.mkdir()
        backup_root.mkdir()
        for action in write_actions:
            staged_skill = stage_root / action.name
            shutil.copytree(action.source, staged_skill)
            staged_issues = validate_skill(staged_skill, transaction_root)
            if staged_issues:
                raise SkillInstallError(
                    f"Staged skill '{action.name}' is invalid:\n{_format_validation_issues(staged_issues)}"
                )

        destination_root.mkdir(parents=True, exist_ok=True)
        for action in write_actions:
            backup = backup_root / action.name if action.target.exists() else None
            if backup is not None:
                _move_path(action.target, backup)
            mutations.append((action.target, backup))
            _move_path(stage_root / action.name, action.target)
    except Exception as exc:
        rollback_errors: list[str] = []
        for target, backup in reversed(mutations):
            try:
                _remove_path(target)
                if backup is not None and backup.exists():
                    _move_path(backup, target)
            except OSError as rollback_exc:
                rollback_errors.append(f"{target}: {rollback_exc}")

        if not destination_existed and destination_root.exists():
            try:
                destination_root.rmdir()
            except OSError as rollback_exc:
                rollback_errors.append(f"{destination_root}: {rollback_exc}")

        detail = f"Skill installation failed; previous destinations restored: {exc}"
        if rollback_errors:
            detail += f"; rollback errors: {'; '.join(rollback_errors)}"
        raise SkillInstallError(detail) from exc
    finally:
        shutil.rmtree(transaction_root, ignore_errors=True)


def print_summary(actions: list[SkillAction], destination_root: Path, *, write: bool, force: bool) -> None:
    print(f"mode: {'write' if write else 'dry-run'}")
    print(f"destination: {destination_root}")
    print(f"force: {force}")
    print()

    for action in actions:
        if action.action == "install":
            verb = "installed" if write else "would install"
        elif action.action == "overwrite":
            verb = "overwritten" if write else "would overwrite"
        elif action.action == "skip-identical":
            verb = "already installed"
        else:
            verb = "conflict"
        print(f"{verb}: {action.name} -> {action.target}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or install repository-local Codex skills.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--dest",
        default="",
        help="Destination skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills.",
    )
    parser.add_argument(
        "--skill",
        action="append",
        dest="skills",
        help="Skill name to install. Repeat or comma-separate. Defaults to all project skills.",
    )
    parser.add_argument("--write", action="store_true", help="Apply changes. Without this flag, only preview.")
    parser.add_argument("--force", action="store_true", help="Overwrite non-matching existing skills.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        root = ensure_repo_root(Path(args.root))
        skills_root = root / "skills"
        destination_root = Path(args.dest).expanduser() if args.dest else default_skills_dest()
        available_skills = discover_project_skills(skills_root, root)
        requested_skills = normalize_requested_skills(args.skills)
        actions = collect_actions(
            available_skills=available_skills,
            requested_skills=requested_skills,
            destination_root=destination_root,
            force=args.force,
        )

        conflicts = [action for action in actions if action.action == "conflict"]
        if conflicts:
            conflict_list = ", ".join(action.name for action in conflicts)
            raise SkillInstallError(f"Existing non-matching skill(s) require --force: {conflict_list}")

        if args.write:
            apply_actions(actions, destination_root)
            print_summary(actions, destination_root, write=True, force=args.force)
        else:
            print_summary(actions, destination_root, write=False, force=args.force)
            print()
            print("preview only; rerun with --write to install")
        return 0
    except (OSError, SkillInstallError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
