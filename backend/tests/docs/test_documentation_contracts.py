import re
from pathlib import Path

from app.core.setup.routers import ROUTER_MODULES
from utils.testing_support.docs import (
    BACKEND_DIR,
    BACKEND_PLAYBOOK_PATH,
    CODE_CHANGE_REQUEST_TEMPLATE_PATH,
    DOCS_DIR,
    FEATURE_REQUEST_TEMPLATE_PATH,
    INTEGRATION_REQUEST_TEMPLATE_PATH,
)

PYTHON_PATH_TOKEN_PATTERN = re.compile(r"`((?:app|utils)/[A-Za-z0-9_./-]+\.py)`")
PLAYBOOK_SECTION_PATTERN_TEMPLATE = r"^## {heading}\s*$"
ROUTER_MODULE_BULLET_PATTERN = re.compile(r"^\-\s+`(?P<module>app\.[A-Za-z0-9_.]+)`\s*$")

REQUIRED_PLAYBOOK_SECTIONS: tuple[str, ...] = (
    "Architecture Map",
    "Router Inventory",
    "Non-Negotiable Engineering Rules",
    "Add a New Feature Workflow",
    "Add a New Integration Workflow",
    "AI Operating Protocol",
    "Reviewer Approval Checklist",
)

REQUIRED_TEMPLATE_SECTIONS: tuple[str, ...] = (
    "Problem and Goal",
    "Scope (In / Out)",
    "API, Data, and Authorization Implications",
    "Observability and Error Handling",
    "Acceptance Criteria",
    "Required Tests",
    "Reviewer Validation Checklist",
)


def _iter_markdown_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.md"))


def _read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_section(markdown: str, heading: str) -> str:
    section_pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<section>[\s\S]*?)(?=^## |\Z)",
        re.MULTILINE,
    )
    section_match = section_pattern.search(markdown)
    assert section_match is not None, f"Section '## {heading}' not found"
    return section_match.group("section")


def test_backend_docs_python_path_references_exist() -> None:
    missing_references: list[str] = []

    for markdown_path in _iter_markdown_files(DOCS_DIR):
        markdown = _read_markdown(markdown_path)
        tokens = {match.group(1) for match in PYTHON_PATH_TOKEN_PATTERN.finditer(markdown)}
        for token in sorted(tokens):
            if "<" in token or ">" in token:
                continue

            resolved_path = BACKEND_DIR / token
            if resolved_path.exists():
                continue

            relative_markdown_path = markdown_path.relative_to(BACKEND_DIR).as_posix()
            missing_references.append(f"{relative_markdown_path} -> {token}")

    assert missing_references == []


def test_backend_playbook_exists_and_has_required_sections() -> None:
    assert BACKEND_PLAYBOOK_PATH.exists()
    markdown = _read_markdown(BACKEND_PLAYBOOK_PATH)

    missing_headings = [
        heading
        for heading in REQUIRED_PLAYBOOK_SECTIONS
        if re.search(PLAYBOOK_SECTION_PATTERN_TEMPLATE.format(heading=re.escape(heading)), markdown, re.MULTILINE)
        is None
    ]
    assert missing_headings == []


def test_backend_playbook_router_inventory_matches_router_catalog() -> None:
    markdown = _read_markdown(BACKEND_PLAYBOOK_PATH)
    router_inventory_section = _extract_section(markdown, "Router Inventory")

    documented_modules = tuple(
        match.group("module")
        for line in router_inventory_section.splitlines()
        for match in [ROUTER_MODULE_BULLET_PATTERN.match(line.strip())]
        if match is not None
    )

    assert documented_modules == ROUTER_MODULES


def test_request_templates_exist_and_have_required_sections() -> None:
    template_paths = (
        FEATURE_REQUEST_TEMPLATE_PATH,
        INTEGRATION_REQUEST_TEMPLATE_PATH,
        CODE_CHANGE_REQUEST_TEMPLATE_PATH,
    )

    missing_files = [path.as_posix() for path in template_paths if not path.exists()]
    assert missing_files == []

    missing_sections: list[str] = []
    for template_path in template_paths:
        markdown = _read_markdown(template_path)
        for heading in REQUIRED_TEMPLATE_SECTIONS:
            if re.search(PLAYBOOK_SECTION_PATTERN_TEMPLATE.format(heading=re.escape(heading)), markdown, re.MULTILINE):
                continue

            missing_sections.append(f"{template_path.relative_to(BACKEND_DIR).as_posix()} -> {heading}")

    assert missing_sections == []
