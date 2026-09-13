from __future__ import annotations

from pathlib import Path

import pytest
from scripts.validate_project_skills import validate_project

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _valid_skill(name: str) -> tuple[str, str]:
    skill = f"""---
name: {name}
description: Validate repository behavior. Use when Codex needs a deterministic project workflow.
---

# {name}

Follow the repository contracts.
"""
    interface = f"""interface:
  display_name: "Example Skill"
  short_description: "Validate a deterministic project workflow"
  default_prompt: "Use ${name} to follow the project workflow."
"""
    return skill, interface


def _repository_fixture(tmp_path: Path, *, skill_names: tuple[str, ...] = ("example-skill",)) -> Path:
    bullets = "\n".join(f"- `skills/{name}`" for name in skill_names)
    headings = "\n\n".join(f"### `{name}`\n\nSkill details." for name in skill_names)
    _write(tmp_path / "AGENTS.md", f"# Agents\n\nProject skill pack:\n\n{bullets}\n")
    _write(tmp_path / "skills" / "README.md", f"# Skills\n\n{headings}\n")
    _write(tmp_path / "docs" / "ai" / "README.md", "# AI Docs\n\n[Agents](../../AGENTS.md)\n")
    for name in skill_names:
        skill, interface = _valid_skill(name)
        _write(tmp_path / "skills" / name / "SKILL.md", skill)
        _write(tmp_path / "skills" / name / "agents" / "openai.yaml", interface)
    return tmp_path


def _codes(root: Path) -> set[str]:
    return {issue.code for issue in validate_project(root)}


def test_valid_project_skill_pack_passes(tmp_path: Path) -> None:
    root = _repository_fixture(tmp_path)
    assert validate_project(root) == []


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    (
        (lambda text: text.removeprefix("---\n"), "frontmatter-missing"),
        (lambda text: text.replace("name: example-skill", "name: wrong-name"), "skill-name-mismatch"),
        (lambda text: text.replace("description:", "license: MIT\ndescription:"), "frontmatter-extra"),
        (lambda text: text.replace("name: example-skill", 'name: "example-skill"'), "frontmatter-scalar"),
    ),
)
def test_frontmatter_negative_contracts(tmp_path: Path, mutation: object, expected_code: str) -> None:
    root = _repository_fixture(tmp_path)
    skill_path = root / "skills" / "example-skill" / "SKILL.md"
    original = skill_path.read_text(encoding="utf-8")
    skill_path.write_text(mutation(original), encoding="utf-8")  # type: ignore[operator]
    assert expected_code in _codes(root)


def test_interface_requires_quoted_strings_and_explicit_invocation(tmp_path: Path) -> None:
    root = _repository_fixture(tmp_path)
    interface_path = root / "skills" / "example-skill" / "agents" / "openai.yaml"
    interface_path.write_text(
        """interface:
  display_name: Example Skill
  short_description: "Validate a deterministic project workflow"
  default_prompt: "Follow the project workflow."
""",
        encoding="utf-8",
    )
    assert {"interface-syntax", "default-prompt-invocation"} <= _codes(root)


def test_catalog_missing_and_extra_skills_are_reported(tmp_path: Path) -> None:
    root = _repository_fixture(tmp_path, skill_names=("example-skill", "second-skill"))
    _write(
        root / "skills" / "README.md",
        "# Skills\n\n### `example-skill`\n\n### `absent-skill`\n",
    )
    assert {"catalog-missing", "catalog-extra"} <= _codes(root)


def test_broken_local_markdown_link_is_reported(tmp_path: Path) -> None:
    root = _repository_fixture(tmp_path)
    _write(root / "docs" / "ai" / "README.md", "# AI Docs\n\n[Missing](missing.md)\n")
    assert "link-missing" in _codes(root)


def test_broken_local_markdown_anchor_is_reported(tmp_path: Path) -> None:
    root = _repository_fixture(tmp_path)
    _write(root / "docs" / "ai" / "README.md", "# AI Docs\n\n[Agents](../../AGENTS.md#missing)\n")
    assert "link-anchor-missing" in _codes(root)


def test_current_pack_passes_project_validator() -> None:
    assert validate_project(REPOSITORY_ROOT) == []
