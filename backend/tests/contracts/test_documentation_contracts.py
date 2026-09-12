import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from app.core.authorization import PERMISSION_ID_PATTERN, READ_ACCESS_LEVELS, ReadAccessLevel
from app.core.authorization.dependencies import allow_authenticated_read_access, allow_public_read_access
from app.core.setup.routers import ROUTER_MODULES
from app.features.auth.dependencies import get_current_user
from app.main import app
from utils.testing_support.docs import (
    BACKEND_DIR,
    BACKEND_PLAYBOOK_PATH,
    CODE_CHANGE_REQUEST_TEMPLATE_PATH,
    DOCS_DIR,
    FEATURE_REQUEST_TEMPLATE_PATH,
    INTEGRATION_REQUEST_TEMPLATE_PATH,
    parse_markdown_table,
)

PYTHON_PATH_TOKEN_PATTERN = re.compile(r"`((?:app|utils)/[A-Za-z0-9_./-]+\.py)`")
PLAYBOOK_SECTION_PATTERN_TEMPLATE = r"^## {heading}\s*$"
ROUTER_MODULE_BULLET_PATTERN = re.compile(r"^\-\s+`(?P<module>app\.[A-Za-z0-9_.]+)`\s*$")
STATUS_CODE_PATTERN = re.compile(r"`(?P<status>[1-5][0-9]{2})`")
HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
EndpointKey = tuple[str, str]
POSTGRES_BACKUP_RUNBOOK_PATH = DOCS_DIR / "operations" / "postgresql_backups.md"
REPOSITORY_ROOT = BACKEND_DIR.parent


@dataclass(frozen=True)
class EndpointContract:
    auth_required: bool
    permission_id: str | None
    success_status: int
    error_statuses: frozenset[int]
    openapi_visible: bool

    @property
    def statuses(self) -> frozenset[int]:
        return frozenset({self.success_status, *self.error_statuses})


@dataclass(frozen=True)
class ReadAccessContract:
    access_level: str
    permission_id: str | None


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


def _strip_code(value: str) -> str:
    return value.removeprefix("`").removesuffix("`")


def _parse_permission(value: str) -> str | None:
    return None if value == "No" else _strip_code(value)


def _parse_endpoint_inventory() -> dict[EndpointKey, EndpointContract]:
    markdown = _read_markdown(DOCS_DIR / "operations" / "api_endpoints.md")
    rows = parse_markdown_table(markdown, heading="Endpoint Summary")
    inventory: dict[EndpointKey, EndpointContract] = {}

    for row in rows:
        endpoint = (_strip_code(row["Method"]), _strip_code(row["Path"]))
        success_statuses = [
            int(match.group("status")) for match in STATUS_CODE_PATTERN.finditer(row["Success Response"])
        ]
        assert len(success_statuses) == 1, f"Expected one success status for {endpoint}, found {success_statuses}"
        error_statuses = frozenset(
            int(match.group("status")) for match in STATUS_CODE_PATTERN.finditer(row["Common Error Statuses"])
        )
        contract = EndpointContract(
            auth_required=row["Auth"] == "Yes",
            permission_id=_parse_permission(row["Permission"]),
            success_status=success_statuses[0],
            error_statuses=error_statuses,
            openapi_visible=row["OpenAPI"] == "Visible",
        )
        assert endpoint not in inventory, f"Duplicate documented endpoint: {endpoint}"
        inventory[endpoint] = contract

    return inventory


def _parse_read_access_inventory() -> dict[EndpointKey, ReadAccessContract]:
    markdown = _read_markdown(DOCS_DIR / "operations" / "api_endpoints.md")
    rows = parse_markdown_table(markdown, heading="Read Access Classification")
    inventory: dict[EndpointKey, ReadAccessContract] = {}
    for row in rows:
        endpoint = (_strip_code(row["Method"]), _strip_code(row["Path"]))
        access_level = _strip_code(row["Access Level"])
        assert access_level in READ_ACCESS_LEVELS
        contract = ReadAccessContract(access_level=access_level, permission_id=_parse_permission(row["Permission"]))
        assert endpoint not in inventory, f"Duplicate documented read endpoint: {endpoint}"
        inventory[endpoint] = contract
    return inventory


def _iter_dependants(root_dependant: Dependant) -> Iterable[Dependant]:
    yield root_dependant
    for child_dependant in root_dependant.dependencies:
        yield from _iter_dependants(child_dependant)


def _route_has_dependency(route: APIRoute, dependency: Callable[..., object]) -> bool:
    return any(dependant.call is dependency for dependant in _iter_dependants(route.dependant))


def _route_permission(route: APIRoute) -> str | None:
    permission_ids: set[str] = set()
    for dependant in _iter_dependants(route.dependant):
        closure = getattr(dependant.call, "__closure__", None)
        for cell in closure or ():
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if isinstance(value, str) and PERMISSION_ID_PATTERN.fullmatch(value):
                permission_ids.add(value)
    assert len(permission_ids) <= 1, f"Multiple permissions found for {route.path}: {sorted(permission_ids)}"
    return next(iter(permission_ids), None)


def _application_routes() -> dict[EndpointKey, APIRoute]:
    routes: dict[EndpointKey, APIRoute] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not getattr(route.endpoint, "__module__", "").startswith("app.features."):
            continue
        for method in (route.methods or set()) & HTTP_METHODS:
            endpoint = (method, route.path)
            assert endpoint not in routes, f"Duplicate runtime endpoint: {endpoint}"
            routes[endpoint] = route
    return routes


def _openapi_operations() -> dict[EndpointKey, Mapping[str, object]]:
    operations: dict[EndpointKey, Mapping[str, object]] = {}
    for path, path_item in app.openapi()["paths"].items():
        assert isinstance(path_item, Mapping)
        for method, operation in path_item.items():
            normalized_method = method.upper()
            if normalized_method not in HTTP_METHODS:
                continue
            assert isinstance(operation, Mapping)
            operations[(normalized_method, path)] = operation
    return operations


def _runtime_read_access(route: APIRoute) -> ReadAccessContract:
    permission_id = _route_permission(route)
    if permission_id is not None:
        return ReadAccessContract(ReadAccessLevel.PERMISSION, permission_id)
    if _route_has_dependency(route, allow_authenticated_read_access):
        return ReadAccessContract(ReadAccessLevel.AUTHENTICATED, None)
    assert _route_has_dependency(route, allow_public_read_access), f"GET {route.path} lacks a read-access marker"
    return ReadAccessContract(ReadAccessLevel.PUBLIC, None)


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


def test_endpoint_inventory_matches_runtime_and_openapi_contracts() -> None:
    documented = _parse_endpoint_inventory()
    runtime = _application_routes()
    openapi = _openapi_operations()

    assert runtime.keys() == documented.keys()
    visible_documented = {endpoint for endpoint, contract in documented.items() if contract.openapi_visible}
    visible_runtime = {endpoint for endpoint, route in runtime.items() if route.include_in_schema}
    assert visible_runtime == visible_documented
    assert openapi.keys() == visible_documented

    for endpoint, route in runtime.items():
        contract = documented[endpoint]
        runtime_statuses = {int(status_code) for status_code in route.responses} | {
            int(route.status_code or HTTPStatus.OK)
        }
        assert runtime_statuses == contract.statuses, f"Runtime status drift for {endpoint}"
        assert _route_has_dependency(route, get_current_user) == contract.auth_required, (
            f"Authentication drift for {endpoint}"
        )
        assert _route_permission(route) == contract.permission_id, f"Permission drift for {endpoint}"

        if contract.openapi_visible:
            responses = openapi[endpoint].get("responses")
            assert isinstance(responses, Mapping)
            openapi_statuses = frozenset(int(status_code) for status_code in responses)
            assert openapi_statuses == contract.statuses, f"OpenAPI status drift for {endpoint}"


def test_read_access_inventory_matches_runtime_routes() -> None:
    documented = _parse_read_access_inventory()
    runtime_reads = {
        endpoint: _runtime_read_access(route)
        for endpoint, route in _application_routes().items()
        if endpoint[0] == "GET"
    }

    assert runtime_reads == documented


def test_postgresql_backup_runbook_is_truthful_and_artifacts_are_excluded() -> None:
    runbook = _read_markdown(POSTGRES_BACKUP_RUNBOOK_PATH)
    required_terms = (
        "Recovery point objective (RPO)",
        "Recovery time objective (RTO)",
        "Retention and expiry policy",
        "Operator and approving owner",
        "Restore-drill cadence",
        "--format=custom",
        "SHA-256",
        "Alembic revision",
        "PostgreSQL server version",
        "pg_restore --username",
        "--exit-on-error",
        "Never restore into the source or production database",
        "does not claim",
        "outside the repository",
        "docker compose down -v",
    )
    assert [term for term in required_terms if term not in runbook] == []

    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
    backend_dockerignore = (BACKEND_DIR / ".dockerignore").read_text(encoding="utf-8")
    frontend_dockerignore = (REPOSITORY_ROOT / "frontend" / ".dockerignore").read_text(encoding="utf-8")
    for pattern in ("backups/", "*.dump", "*.backup", "*.sql.gz", "*.dump.sha256"):
        assert pattern in gitignore
    for pattern in ("*.dump", "*.backup", "*.sql.gz", "*.dump.sha256"):
        assert pattern in backend_dockerignore
        assert pattern in frontend_dockerignore
