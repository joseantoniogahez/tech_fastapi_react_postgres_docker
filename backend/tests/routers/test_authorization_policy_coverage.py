import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from app.const.permission import PERMISSION_ID_PATTERN
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[2]
AUTHORIZATION_MATRIX_PATH = BACKEND_DIR / "docs" / "authorization_matrix.md"
API_ENDPOINTS_PATH = BACKEND_DIR / "docs" / "api_endpoints.md"

HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
SECTION_PATTERN_TEMPLATE = r"^## {heading}\n(?P<section>[\s\S]*?)(?=^## |\Z)"

AUTHORIZATION_MATRIX_ROW_PATTERN = re.compile(
    r"^\|\s*`(?P<method>[A-Z]+)`\s*\|\s*`(?P<path>/[^`]+)`\s*\|\s*"
    r"`(?P<permission_id>[a-z][a-z0-9_]*:[a-z][a-z0-9_]*)`\s*\|\s*"
    r"`(?P<dependency_alias>[A-Za-z_][A-Za-z0-9_]*)`\s*\|$"
)
API_ENDPOINT_SUMMARY_ROW_PATTERN = re.compile(
    r"^\|\s*`(?P<method>[A-Z]+)`\s*\|\s*`(?P<path>/[^`]+)`\s*\|\s*"
    r"(?P<auth>Yes|No)\s*\|\s*"
    r"(?P<permission_cell>`[a-z][a-z0-9_]*:[a-z][a-z0-9_]*`|No)\s*\|"
)

EndpointKey = tuple[str, str]


@dataclass(frozen=True)
class ApiEndpointDocRow:
    auth_required: bool
    permission_id: str | None


def _format_endpoint(endpoint: EndpointKey) -> str:
    return f"{endpoint[0]} {endpoint[1]}"


def _extract_section(markdown: str, heading: str) -> str:
    section_pattern = re.compile(SECTION_PATTERN_TEMPLATE.format(heading=re.escape(heading)), re.MULTILINE)
    section_match = section_pattern.search(markdown)
    assert section_match is not None, f"Section '## {heading}' not found in markdown contract"
    return section_match.group("section")


def _iter_dependants(root_dependant: Dependant) -> Iterable[Dependant]:
    yield root_dependant
    for child_dependant in root_dependant.dependencies:
        yield from _iter_dependants(child_dependant)


def _extract_permission_id_from_dependency_callable(dependency_call: Callable[..., object]) -> str | None:
    closure = getattr(dependency_call, "__closure__", None)
    if closure is None:
        return None

    for cell in closure:
        try:
            cell_value = cell.cell_contents
        except ValueError:
            continue
        if isinstance(cell_value, str) and PERMISSION_ID_PATTERN.fullmatch(cell_value):
            return cell_value

    return None


def _collect_route_permission_ids(route: APIRoute) -> set[str]:
    permission_ids: set[str] = set()
    for dependant in _iter_dependants(route.dependant):
        dependency_call = dependant.call
        if dependency_call is None:
            continue
        permission_id = _extract_permission_id_from_dependency_callable(dependency_call)
        if permission_id is not None:
            permission_ids.add(permission_id)
    return permission_ids


def _collect_protected_endpoints_from_routes() -> dict[EndpointKey, str]:
    protected_endpoints: dict[EndpointKey, str] = {}

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        permission_ids = _collect_route_permission_ids(route)
        if not permission_ids:
            continue

        assert len(permission_ids) == 1, (
            "Each protected endpoint must have exactly one permission. "
            f"Found {sorted(permission_ids)} for route {route.path}"
        )
        permission_id = next(iter(permission_ids))

        route_methods = sorted((route.methods or set()) & HTTP_METHODS)
        for method in route_methods:
            endpoint = (method, route.path)
            previous_permission = protected_endpoints.get(endpoint)
            assert previous_permission in (None, permission_id), (
                f"Conflicting permissions detected for endpoint {_format_endpoint(endpoint)}: "
                f"{previous_permission} vs {permission_id}"
            )
            protected_endpoints[endpoint] = permission_id

    assert protected_endpoints, "No protected endpoints discovered from router dependencies"
    return protected_endpoints


def _parse_authorization_matrix_inventory(path: Path) -> dict[EndpointKey, str]:
    matrix_markdown = path.read_text(encoding="utf-8")
    matrix_section = _extract_section(matrix_markdown, "Protected Endpoint Inventory")

    endpoint_permissions: dict[EndpointKey, str] = {}
    for line in matrix_section.splitlines():
        row_match = AUTHORIZATION_MATRIX_ROW_PATTERN.match(line.strip())
        if row_match is None:
            continue

        endpoint = (row_match.group("method"), row_match.group("path"))
        permission_id = row_match.group("permission_id")
        previous_permission = endpoint_permissions.get(endpoint)
        assert previous_permission in (None, permission_id), (
            f"Duplicate endpoint mapping with conflicting permissions in {path}: "
            f"{_format_endpoint(endpoint)} -> {previous_permission} vs {permission_id}"
        )
        endpoint_permissions[endpoint] = permission_id

    assert endpoint_permissions, f"No protected endpoint rows parsed from {path}"
    return endpoint_permissions


def _parse_api_endpoint_summary(path: Path) -> dict[EndpointKey, ApiEndpointDocRow]:
    api_endpoints_markdown = path.read_text(encoding="utf-8")
    summary_section = _extract_section(api_endpoints_markdown, "Endpoint Summary")

    endpoint_rows: dict[EndpointKey, ApiEndpointDocRow] = {}
    for line in summary_section.splitlines():
        row_match = API_ENDPOINT_SUMMARY_ROW_PATTERN.match(line.strip())
        if row_match is None:
            continue

        endpoint = (row_match.group("method"), row_match.group("path"))
        permission_cell = row_match.group("permission_cell")
        permission_id = permission_cell.removeprefix("`").removesuffix("`") if permission_cell != "No" else None
        row = ApiEndpointDocRow(auth_required=row_match.group("auth") == "Yes", permission_id=permission_id)

        previous_row = endpoint_rows.get(endpoint)
        assert previous_row in (None, row), f"Duplicate endpoint row in {path}: {_format_endpoint(endpoint)}"
        endpoint_rows[endpoint] = row

    assert endpoint_rows, f"No endpoint summary rows parsed from {path}"
    return endpoint_rows


def _assert_endpoint_permission_contract(
    actual_protected_endpoints: dict[EndpointKey, str],
    documented_protected_endpoints: dict[EndpointKey, str],
    *,
    source_name: str,
) -> None:
    missing_endpoints = sorted(
        endpoint for endpoint in actual_protected_endpoints if endpoint not in documented_protected_endpoints
    )
    permission_mismatches = sorted(
        (
            endpoint,
            actual_protected_endpoints[endpoint],
            documented_protected_endpoints[endpoint],
        )
        for endpoint in actual_protected_endpoints
        if endpoint in documented_protected_endpoints
        and documented_protected_endpoints[endpoint] != actual_protected_endpoints[endpoint]
    )
    stale_documented_endpoints = sorted(
        endpoint for endpoint in documented_protected_endpoints if endpoint not in actual_protected_endpoints
    )

    error_messages: list[str] = []
    if missing_endpoints:
        missing_text = ", ".join(_format_endpoint(endpoint) for endpoint in missing_endpoints)
        error_messages.append(f"Missing protected endpoint mappings in {source_name}: {missing_text}")

    if permission_mismatches:
        mismatch_text = ", ".join(
            f"{_format_endpoint(endpoint)} expected {actual_permission} documented {documented_permission}"
            for endpoint, actual_permission, documented_permission in permission_mismatches
        )
        error_messages.append(f"Permission mismatches in {source_name}: {mismatch_text}")

    if stale_documented_endpoints:
        stale_text = ", ".join(_format_endpoint(endpoint) for endpoint in stale_documented_endpoints)
        error_messages.append(f"Stale documented protected endpoints in {source_name}: {stale_text}")

    assert not error_messages, "\n".join(error_messages)


def test_authorization_matrix_matches_protected_router_endpoints() -> None:
    actual_protected_endpoints = _collect_protected_endpoints_from_routes()
    documented_protected_endpoints = _parse_authorization_matrix_inventory(AUTHORIZATION_MATRIX_PATH)

    _assert_endpoint_permission_contract(
        actual_protected_endpoints,
        documented_protected_endpoints,
        source_name=AUTHORIZATION_MATRIX_PATH.name,
    )


def test_api_endpoints_document_protected_router_permissions() -> None:
    actual_protected_endpoints = _collect_protected_endpoints_from_routes()
    endpoint_summary = _parse_api_endpoint_summary(API_ENDPOINTS_PATH)

    missing_endpoints = sorted(endpoint for endpoint in actual_protected_endpoints if endpoint not in endpoint_summary)
    auth_mismatches = sorted(
        endpoint
        for endpoint in actual_protected_endpoints
        if endpoint in endpoint_summary and not endpoint_summary[endpoint].auth_required
    )
    permission_mismatches = sorted(
        (
            endpoint,
            actual_protected_endpoints[endpoint],
            endpoint_summary[endpoint].permission_id,
        )
        for endpoint in actual_protected_endpoints
        if endpoint in endpoint_summary
        and endpoint_summary[endpoint].permission_id != actual_protected_endpoints[endpoint]
    )

    documented_protected_endpoints = {
        endpoint: row.permission_id for endpoint, row in endpoint_summary.items() if row.permission_id is not None
    }
    stale_documented_endpoints = sorted(
        endpoint for endpoint in documented_protected_endpoints if endpoint not in actual_protected_endpoints
    )

    error_messages: list[str] = []
    if missing_endpoints:
        missing_text = ", ".join(_format_endpoint(endpoint) for endpoint in missing_endpoints)
        error_messages.append(f"Missing endpoint rows in {API_ENDPOINTS_PATH.name}: {missing_text}")

    if auth_mismatches:
        auth_text = ", ".join(_format_endpoint(endpoint) for endpoint in auth_mismatches)
        error_messages.append(f"Protected endpoints must be marked Auth=Yes in {API_ENDPOINTS_PATH.name}: {auth_text}")

    if permission_mismatches:
        mismatch_text = ", ".join(
            f"{_format_endpoint(endpoint)} expected {actual_permission} documented {documented_permission}"
            for endpoint, actual_permission, documented_permission in permission_mismatches
        )
        error_messages.append(f"Permission mismatches in {API_ENDPOINTS_PATH.name}: {mismatch_text}")

    if stale_documented_endpoints:
        stale_text = ", ".join(_format_endpoint(endpoint) for endpoint in stale_documented_endpoints)
        error_messages.append(f"Stale permission-mapped endpoints in {API_ENDPOINTS_PATH.name}: {stale_text}")

    assert not error_messages, "\n".join(error_messages)
