#!/usr/bin/env python3
"""Validate the repository-local Codex skill pack without third-party parsers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
FRONTMATTER_FIELD_PATTERN = re.compile(r"^(?P<key>[a-z_]+): (?P<value>.+)$")
INTERFACE_FIELD_PATTERN = re.compile(r'^  (?P<key>[a-z_]+): (?P<value>"(?:[^"\\]|\\.)*")$')
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\((?P<target>[^)]+)\)")
AGENTS_SKILL_PATTERN = re.compile(r"^- `skills/(?P<name>[a-z0-9-]+)`$", re.MULTILINE)
CATALOG_SKILL_PATTERN = re.compile(r"^### `(?P<name>[a-z0-9-]+)`$", re.MULTILINE)

FRONTMATTER_FIELDS = ("name", "description")
INTERFACE_FIELDS = ("display_name", "short_description", "default_prompt")


@dataclass(frozen=True, order=True)
class ValidationIssue:
    path: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: [{self.code}] {self.message}"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(path: Path, root: Path, issues: list[ValidationIssue]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        issues.append(ValidationIssue(_relative(path, root), "unreadable", str(exc)))
        return None


def _parse_frontmatter(path: Path, root: Path, issues: list[ValidationIssue]) -> dict[str, str] | None:
    text = _read_text(path, root, issues)
    if text is None:
        return None
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        issues.append(
            ValidationIssue(_relative(path, root), "frontmatter-missing", "SKILL.md must start with '---'.")
        )
        return None
    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        issues.append(
            ValidationIssue(_relative(path, root), "frontmatter-unclosed", "Frontmatter needs a closing '---'.")
        )
        return None

    values: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        match = FRONTMATTER_FIELD_PATTERN.fullmatch(line)
        if match is None:
            issues.append(
                ValidationIssue(
                    _relative(path, root),
                    "frontmatter-syntax",
                    f"Line {line_number} must be an unindented single-line 'key: value' scalar.",
                )
            )
            continue
        key = match.group("key")
        value = match.group("value").strip()
        if key in values:
            issues.append(
                ValidationIssue(_relative(path, root), "frontmatter-duplicate", f"Duplicate field '{key}'.")
            )
            continue
        if value.startswith(("'", '"', "[", "{", "|", ">", "&", "*", "!")) or " #" in value:
            issues.append(
                ValidationIssue(
                    _relative(path, root),
                    "frontmatter-scalar",
                    f"Field '{key}' must use the portable unquoted single-line scalar grammar.",
                )
            )
            continue
        values[key] = value

    actual_fields = set(values)
    expected_fields = set(FRONTMATTER_FIELDS)
    for key in sorted(actual_fields - expected_fields):
        issues.append(ValidationIssue(_relative(path, root), "frontmatter-extra", f"Unexpected field '{key}'."))
    for key in sorted(expected_fields - actual_fields):
        issues.append(ValidationIssue(_relative(path, root), "frontmatter-required", f"Missing field '{key}'."))
    if closing_index + 1 >= len(lines) or not any(line.strip() for line in lines[closing_index + 1 :]):
        issues.append(ValidationIssue(_relative(path, root), "skill-body-empty", "SKILL.md body is empty."))
    return values


def _parse_interface(path: Path, root: Path, issues: list[ValidationIssue]) -> dict[str, str] | None:
    text = _read_text(path, root, issues)
    if text is None:
        return None
    lines = text.splitlines()
    if not lines or lines[0] != "interface:":
        issues.append(
            ValidationIssue(_relative(path, root), "interface-root", "Metadata must start with 'interface:'.")
        )
        return None

    values: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        match = INTERFACE_FIELD_PATTERN.fullmatch(line)
        if match is None:
            issues.append(
                ValidationIssue(
                    _relative(path, root),
                    "interface-syntax",
                    f"Line {line_number} must be a two-space-indented key with a double-quoted string.",
                )
            )
            continue
        key = match.group("key")
        if key in values:
            issues.append(ValidationIssue(_relative(path, root), "interface-duplicate", f"Duplicate field '{key}'."))
            continue
        values[key] = json.loads(match.group("value"))

    actual_fields = set(values)
    expected_fields = set(INTERFACE_FIELDS)
    for key in sorted(actual_fields - expected_fields):
        issues.append(ValidationIssue(_relative(path, root), "interface-extra", f"Unexpected field '{key}'."))
    for key in sorted(expected_fields - actual_fields):
        issues.append(ValidationIssue(_relative(path, root), "interface-required", f"Missing field '{key}'."))
    return values


def validate_skill(skill_dir: Path, root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    skill_name = skill_dir.name
    skill_path = skill_dir / "SKILL.md"
    interface_path = skill_dir / "agents" / "openai.yaml"

    if not skill_path.is_file():
        issues.append(ValidationIssue(_relative(skill_path, root), "skill-file-missing", "SKILL.md is required."))
        frontmatter = None
    else:
        frontmatter = _parse_frontmatter(skill_path, root, issues)

    if not interface_path.is_file():
        issues.append(
            ValidationIssue(_relative(interface_path, root), "interface-file-missing", "agents/openai.yaml is required.")
        )
        interface = None
    else:
        interface = _parse_interface(interface_path, root, issues)

    if not SKILL_NAME_PATTERN.fullmatch(skill_name) or "--" in skill_name:
        issues.append(
            ValidationIssue(_relative(skill_dir, root), "skill-name-invalid", "Folder name must use lowercase kebab-case.")
        )
    if frontmatter is not None:
        if frontmatter.get("name") != skill_name:
            issues.append(
                ValidationIssue(
                    _relative(skill_path, root),
                    "skill-name-mismatch",
                    f"Frontmatter name must equal folder name '{skill_name}'.",
                )
            )
        description = frontmatter.get("description", "")
        if not 20 <= len(description) <= 512 or "use when" not in description.lower():
            issues.append(
                ValidationIssue(
                    _relative(skill_path, root),
                    "description-trigger",
                    "Description must be 20-512 characters and include an explicit 'Use when' trigger.",
                )
            )
    if interface is not None:
        short_description = interface.get("short_description", "")
        if not 10 <= len(short_description) <= 80:
            issues.append(
                ValidationIssue(
                    _relative(interface_path, root),
                    "short-description-length",
                    "short_description must contain 10-80 characters.",
                )
            )
        default_prompt = interface.get("default_prompt", "")
        if f"${skill_name}" not in default_prompt:
            issues.append(
                ValidationIssue(
                    _relative(interface_path, root),
                    "default-prompt-invocation",
                    f"default_prompt must explicitly mention '${skill_name}'.",
                )
            )
    return issues


def _heading_anchors(markdown: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in markdown.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
        if match is None:
            continue
        anchor = match.group(1).strip().lower()
        anchor = re.sub(r"[`*_~]", "", anchor)
        anchor = re.sub(r"[^\w\- ]", "", anchor, flags=re.UNICODE)
        anchor = re.sub(r"\s", "-", anchor).strip("-")
        count = counts.get(anchor, 0)
        counts[anchor] = count + 1
        anchors.add(anchor if count == 0 else f"{anchor}-{count}")
    return anchors


def validate_markdown_links(root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    markdown_paths = [root / "AGENTS.md", root / "skills" / "README.md"]
    markdown_paths.extend(sorted((root / "docs" / "ai").rglob("*.md")))
    for markdown_path in markdown_paths:
        if not markdown_path.is_file():
            continue
        markdown = _read_text(markdown_path, root, issues)
        if markdown is None:
            continue
        for match in MARKDOWN_LINK_PATTERN.finditer(markdown):
            raw_target = match.group("target").strip()
            if raw_target.startswith("<") and raw_target.endswith(">"):
                raw_target = raw_target[1:-1]
            if raw_target.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, _, fragment = raw_target.partition("#")
            target_path = markdown_path if not path_part else markdown_path.parent / unquote(path_part)
            target_path = target_path.resolve()
            if not target_path.exists():
                issues.append(
                    ValidationIssue(
                        _relative(markdown_path, root), "link-missing", f"Local link target does not exist: {raw_target}"
                    )
                )
                continue
            if fragment and target_path.is_file() and target_path.suffix.lower() == ".md":
                target_markdown = _read_text(target_path, root, issues)
                if target_markdown is not None and unquote(fragment).lower() not in _heading_anchors(target_markdown):
                    issues.append(
                        ValidationIssue(
                            _relative(markdown_path, root),
                            "link-anchor-missing",
                            f"Markdown anchor does not exist: {raw_target}",
                        )
                    )
    return issues


def validate_catalogs(root: Path, filesystem_skills: set[str]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    agents_path = root / "AGENTS.md"
    catalog_path = root / "skills" / "README.md"
    agents_text = _read_text(agents_path, root, issues) or ""
    catalog_text = _read_text(catalog_path, root, issues) or ""
    agents_skills = set(AGENTS_SKILL_PATTERN.findall(agents_text))
    catalog_skills = set(CATALOG_SKILL_PATTERN.findall(catalog_text))
    for label, path, names in (
        ("AGENTS.md", agents_path, agents_skills),
        ("skills/README.md", catalog_path, catalog_skills),
    ):
        missing = sorted(filesystem_skills - names)
        extra = sorted(names - filesystem_skills)
        if missing:
            issues.append(
                ValidationIssue(_relative(path, root), "catalog-missing", f"{label} omits skills: {', '.join(missing)}")
            )
        if extra:
            issues.append(
                ValidationIssue(_relative(path, root), "catalog-extra", f"{label} lists absent skills: {', '.join(extra)}")
            )
    return issues


def validate_project(root: Path) -> list[ValidationIssue]:
    root = root.resolve()
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return [ValidationIssue("skills", "skills-root-missing", "skills directory is required.")]
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    filesystem_skills = {path.name for path in skill_dirs}
    issues = [issue for skill_dir in skill_dirs for issue in validate_skill(skill_dir, root)]
    issues.extend(validate_catalogs(root, filesystem_skills))
    issues.extend(validate_markdown_links(root))
    return sorted(set(issues))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate repository-local Codex skills and governance links.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to the current directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if not root.exists():
        print(f"error: repository root does not exist: {root}", file=sys.stderr)
        return 2
    issues = validate_project(root)
    for issue in issues:
        print(issue)
    if issues:
        print(f"validation failed: {len(issues)} issue(s)", file=sys.stderr)
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
