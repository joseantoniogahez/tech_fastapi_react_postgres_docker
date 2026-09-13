from collections.abc import Mapping
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = BACKEND_DIR / "docs"
OPERATIONS_DOCS_DIR = DOCS_DIR / "operations"
TEMPLATES_DOCS_DIR = DOCS_DIR / "templates"

BACKEND_PLAYBOOK_PATH = DOCS_DIR / "backend_playbook.md"
AUTHORIZATION_MATRIX_PATH = OPERATIONS_DOCS_DIR / "authorization_matrix.md"
API_ENDPOINTS_PATH = OPERATIONS_DOCS_DIR / "api_endpoints.md"
FEATURE_REQUEST_TEMPLATE_PATH = TEMPLATES_DOCS_DIR / "feature_request.md"
INTEGRATION_REQUEST_TEMPLATE_PATH = TEMPLATES_DOCS_DIR / "integration_request.md"
CODE_CHANGE_REQUEST_TEMPLATE_PATH = TEMPLATES_DOCS_DIR / "code_change_request.md"


def extract_markdown_section(markdown: str, heading: str) -> str:
    lines = markdown.splitlines()
    section_start: int | None = None

    for index, line in enumerate(lines):
        if line == f"## {heading}":
            section_start = index + 1
            break

    if section_start is None:
        raise AssertionError(f"Section '## {heading}' not found in markdown contract")

    section_end = next(
        (index for index in range(section_start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[section_start:section_end])


def parse_markdown_table(markdown: str, *, heading: str) -> list[Mapping[str, str]]:
    section_lines = extract_markdown_section(markdown, heading).splitlines()
    table_lines = [line.strip() for line in section_lines if line.strip().startswith("|")]
    if len(table_lines) < 2:
        raise AssertionError(f"Markdown table not found below '## {heading}'")

    def parse_cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip("|").split("|")]

    headers = parse_cells(table_lines[0])
    separator = parse_cells(table_lines[1])
    if len(headers) != len(separator) or any(set(cell) - {"-", ":"} for cell in separator):
        raise AssertionError(f"Invalid Markdown table header below '## {heading}'")
    if len(headers) != len(set(headers)):
        raise AssertionError(f"Duplicate Markdown table headers below '## {heading}'")

    rows: list[Mapping[str, str]] = []
    for line in table_lines[2:]:
        cells = parse_cells(line)
        if len(cells) != len(headers):
            raise AssertionError(f"Invalid Markdown table row below '## {heading}': {line}")
        rows.append(dict(zip(headers, cells, strict=True)))

    if not rows:
        raise AssertionError(f"Markdown table below '## {heading}' has no data rows")
    return rows
