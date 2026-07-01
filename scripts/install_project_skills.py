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
from dataclasses import dataclass
from pathlib import Path

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


def discover_project_skills(skills_root: Path) -> dict[str, Path]:
    skills: dict[str, Path] = {}
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "SKILL.md").is_file():
            continue
        skills[child.name] = child
    if not skills:
        raise SkillInstallError(f"No skills found in {skills_root}")
    return skills


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


def apply_actions(actions: list[SkillAction], destination_root: Path) -> None:
    destination_root.mkdir(parents=True, exist_ok=True)

    for action in actions:
        if action.action == "skip-identical":
            continue
        if action.action == "conflict":
            raise SkillInstallError(f"Refusing to overwrite existing skill without --force: {action.target}")

        assert_target_within_destination(action.target, destination_root)

        if action.target.exists():
            if action.target.is_dir():
                shutil.rmtree(action.target)
            else:
                action.target.unlink()

        shutil.copytree(action.source, action.target)


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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        root = ensure_repo_root(Path(args.root))
        skills_root = root / "skills"
        destination_root = Path(args.dest).expanduser() if args.dest else default_skills_dest()
        available_skills = discover_project_skills(skills_root)
        requested_skills = normalize_requested_skills(args.skills)
        actions = collect_actions(
            available_skills=available_skills,
            requested_skills=requested_skills,
            destination_root=destination_root,
            force=args.force,
        )

        print_summary(actions, destination_root, write=args.write, force=args.force)

        conflicts = [action for action in actions if action.action == "conflict"]
        if conflicts:
            conflict_list = ", ".join(action.name for action in conflicts)
            raise SkillInstallError(f"Existing non-matching skill(s) require --force: {conflict_list}")

        if args.write:
            apply_actions(actions, destination_root)
        else:
            print()
            print("preview only; rerun with --write to install")
        return 0
    except SkillInstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
