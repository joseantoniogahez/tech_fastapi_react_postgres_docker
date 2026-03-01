import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from app.const.permission import (
    PERMISSION_ID_PATTERN,
    PERMISSION_SCOPES,
    READ_ACCESS_LEVELS,
    READ_ACCESS_POLICY_CATALOG,
    PermissionScope,
    ReadAccessLevel,
)
from app.dependencies.authorization import allow_authenticated_read_access, allow_public_read_access
from app.main import app
from utils.testing_support.docs import API_ENDPOINTS_PATH, AUTHORIZATION_MATRIX_PATH

HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
SECTION_PATTERN_TEMPLATE = r"^## {heading}\n(?P<section>[\s\S]*?)(?=^## |\Z)"

AUTHORIZATION_MATRIX_ROW_PATTERN = re.compile(
    r"^\|\s*`(?P<method>[A-Z]+)`\s*\|\s*`(?P<path>/[^`]+)`\s*\|\s*"
    r"`(?P<permission_id>[a-z][a-z0-9_]*:[a-z][a-z0-9_]*)`\s*\|\s*"
    r"`(?P<required_scope>own|tenant|any)`\s*\|\s*"
    r"`(?P<dependency_alias>[A-Za-z_][A-Za-z0-9_]*)`\s*\|$"
)
API_ENDPOINT_SUMMARY_ROW_PATTERN = re.compile(
    r"^\|\s*`(?P<method>[A-Z]+)`\s*\|\s*`(?P<path>/[^`]+)`\s*\|\s*"
    r"(?P<auth>Yes|No)\s*\|\s*"
    r"(?P<permission_cell>`[a-z][a-z0-9_]*:[a-z][a-z0-9_]*`|No)\s*\|"
)
READ_ACCESS_ROW_PATTERN = re.compile(
    r"^\|\s*`(?P<method>GET)`\s*\|\s*`(?P<path>/[^`]+)`\s*\|\s*"
    r"`(?P<access_level>public|authenticated|permission)`\s*\|\s*"
    r"(?P<permission_cell>`[a-z][a-z0-9_]*:[a-z][a-z0-9_]*`|No)\s*\|$"
)

EndpointKey = tuple[str, str]


@dataclass(frozen=True)
class ApiEndpointDocRow:
    auth_required: bool
    permission_id: str | None


@dataclass(frozen=True)
class ProtectedEndpointPolicyRow:
    permission_id: str
    required_scope: str


@dataclass(frozen=True)
class ReadAccessPolicyRow:
    access_level: str
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


def _extract_required_scope_from_dependency_callable(dependency_call: Callable[..., object]) -> str | None:
    closure = getattr(dependency_call, "__closure__", None)
    if closure is None:
        return None

    for cell in closure:
        try:
            cell_value = cell.cell_contents
        except ValueError:
            continue
        if isinstance(cell_value, str) and cell_value in PERMISSION_SCOPES:
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


def _collect_route_permission_scopes(route: APIRoute) -> set[str]:
    required_scopes: set[str] = set()
    for dependant in _iter_dependants(route.dependant):
        dependency_call = dependant.call
        if dependency_call is None:
            continue
        required_scope = _extract_required_scope_from_dependency_callable(dependency_call)
        if required_scope is not None:
            required_scopes.add(required_scope)
    return required_scopes


def _is_application_router_route(route: APIRoute) -> bool:
    route_module = getattr(route.endpoint, "__module__", "")
    return route_module.startswith("app.routers.")


def _route_has_dependency_callable(route: APIRoute, dependency_callable: Callable[..., object]) -> bool:
    for dependant in _iter_dependants(route.dependant):
        if dependant.call is dependency_callable:
            return True
    return False


def _collect_protected_endpoints_from_routes() -> dict[EndpointKey, ProtectedEndpointPolicyRow]:
    protected_endpoints: dict[EndpointKey, ProtectedEndpointPolicyRow] = {}

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not _is_application_router_route(route):
            continue

        permission_ids = _collect_route_permission_ids(route)
        if not permission_ids:
            continue
        required_scopes = _collect_route_permission_scopes(route)

        assert len(permission_ids) == 1, (
            "Each protected endpoint must have exactly one permission. "
            f"Found {sorted(permission_ids)} for route {route.path}"
        )
        permission_id = next(iter(permission_ids))
        if required_scopes:
            assert len(required_scopes) == 1, (
                "Each protected endpoint must resolve to exactly one required scope. "
                f"Found {sorted(required_scopes)} for route {route.path}"
            )
            required_scope = next(iter(required_scopes))
        else:
            required_scope = PermissionScope.ANY

        policy_row = ProtectedEndpointPolicyRow(
            permission_id=permission_id,
            required_scope=required_scope,
        )

        route_methods = sorted((route.methods or set()) & HTTP_METHODS)
        for method in route_methods:
            endpoint = (method, route.path)
            previous_policy = protected_endpoints.get(endpoint)
            assert previous_policy in (None, policy_row), (
                f"Conflicting permission policies detected for endpoint {_format_endpoint(endpoint)}: "
                f"{previous_policy} vs {policy_row}"
            )
            protected_endpoints[endpoint] = policy_row

    assert protected_endpoints, "No protected endpoints discovered from router dependencies"
    return protected_endpoints


def _collect_read_endpoint_policies_from_routes() -> dict[EndpointKey, ReadAccessPolicyRow]:
    read_policies: dict[EndpointKey, ReadAccessPolicyRow] = {}

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not _is_application_router_route(route):
            continue
        if "GET" not in (route.methods or set()):
            continue

        endpoint = ("GET", route.path)
        permission_ids = _collect_route_permission_ids(route)
        has_public_policy = _route_has_dependency_callable(route, allow_public_read_access)
        has_authenticated_policy = _route_has_dependency_callable(route, allow_authenticated_read_access)

        policy_markers = int(bool(permission_ids)) + int(has_public_policy) + int(has_authenticated_policy)
        assert policy_markers == 1, (
            "Each read endpoint must be explicitly classified with exactly one policy marker: "
            "public, authenticated, or permission-based. "
            f"Found permission_ids={sorted(permission_ids)} public={has_public_policy} "
            f"authenticated={has_authenticated_policy} for route {route.path}"
        )

        if permission_ids:
            assert len(permission_ids) == 1, (
                "Permission-based read endpoints must have exactly one permission. "
                f"Found {sorted(permission_ids)} for route {route.path}"
            )
            policy_row = ReadAccessPolicyRow(
                access_level=ReadAccessLevel.PERMISSION,
                permission_id=next(iter(permission_ids)),
            )
        elif has_authenticated_policy:
            policy_row = ReadAccessPolicyRow(
                access_level=ReadAccessLevel.AUTHENTICATED,
                permission_id=None,
            )
        else:
            policy_row = ReadAccessPolicyRow(
                access_level=ReadAccessLevel.PUBLIC,
                permission_id=None,
            )

        previous_row = read_policies.get(endpoint)
        assert previous_row in (None, policy_row), f"Conflicting read policy markers for {_format_endpoint(endpoint)}"
        read_policies[endpoint] = policy_row

    assert read_policies, "No read endpoints discovered from router dependencies"
    return read_policies


def _collect_read_endpoint_policies_from_catalog() -> dict[EndpointKey, ReadAccessPolicyRow]:
    read_policies: dict[EndpointKey, ReadAccessPolicyRow] = {}
    for policy in READ_ACCESS_POLICY_CATALOG:
        endpoint = policy.endpoint
        policy_row = ReadAccessPolicyRow(access_level=policy.access_level, permission_id=policy.permission_id)

        previous_row = read_policies.get(endpoint)
        assert previous_row in (None, policy_row), (
            "Duplicate read-access policy with conflicting values in READ_ACCESS_POLICY_CATALOG for endpoint "
            f"{_format_endpoint(endpoint)}"
        )
        read_policies[endpoint] = policy_row

    assert read_policies, "READ_ACCESS_POLICY_CATALOG must define at least one endpoint"
    return read_policies


def _parse_authorization_matrix_inventory(path: Path) -> dict[EndpointKey, ProtectedEndpointPolicyRow]:
    matrix_markdown = path.read_text(encoding="utf-8")
    matrix_section = _extract_section(matrix_markdown, "Protected Endpoint Inventory")

    endpoint_policies: dict[EndpointKey, ProtectedEndpointPolicyRow] = {}
    for line in matrix_section.splitlines():
        row_match = AUTHORIZATION_MATRIX_ROW_PATTERN.match(line.strip())
        if row_match is None:
            continue

        endpoint = (row_match.group("method"), row_match.group("path"))
        policy_row = ProtectedEndpointPolicyRow(
            permission_id=row_match.group("permission_id"),
            required_scope=row_match.group("required_scope"),
        )
        previous_policy = endpoint_policies.get(endpoint)
        assert previous_policy in (None, policy_row), (
            f"Duplicate endpoint mapping with conflicting policies in {path}: "
            f"{_format_endpoint(endpoint)} -> {previous_policy} vs {policy_row}"
        )
        endpoint_policies[endpoint] = policy_row

    assert endpoint_policies, f"No protected endpoint rows parsed from {path}"
    return endpoint_policies


def _parse_read_access_policy_section(path: Path, *, heading: str) -> dict[EndpointKey, ReadAccessPolicyRow]:
    markdown = path.read_text(encoding="utf-8")
    section = _extract_section(markdown, heading)

    endpoint_rows: dict[EndpointKey, ReadAccessPolicyRow] = {}
    for line in section.splitlines():
        row_match = READ_ACCESS_ROW_PATTERN.match(line.strip())
        if row_match is None:
            continue

        endpoint = (row_match.group("method"), row_match.group("path"))
        access_level = row_match.group("access_level")
        permission_cell = row_match.group("permission_cell")
        permission_id = permission_cell.removeprefix("`").removesuffix("`") if permission_cell != "No" else None
        assert (
            access_level in READ_ACCESS_LEVELS
        ), f"Invalid documented access level '{access_level}' for endpoint {_format_endpoint(endpoint)} in {path}"

        endpoint_row = ReadAccessPolicyRow(access_level=access_level, permission_id=permission_id)
        previous_row = endpoint_rows.get(endpoint)
        assert previous_row in (None, endpoint_row), f"Duplicate endpoint row in {path}: {_format_endpoint(endpoint)}"
        endpoint_rows[endpoint] = endpoint_row

    assert endpoint_rows, f"No read-access policy rows parsed from {path} section '{heading}'"
    return endpoint_rows


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
    actual_protected_endpoints: dict[EndpointKey, ProtectedEndpointPolicyRow],
    documented_protected_endpoints: dict[EndpointKey, ProtectedEndpointPolicyRow],
    *,
    source_name: str,
) -> None:
    missing_endpoints = sorted(
        endpoint for endpoint in actual_protected_endpoints if endpoint not in documented_protected_endpoints
    )
    policy_mismatches = sorted(
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

    if policy_mismatches:
        mismatch_text = ", ".join(
            (
                f"{_format_endpoint(endpoint)} expected "
                f"({actual_policy.permission_id}, {actual_policy.required_scope}) "
                f"documented ({documented_policy.permission_id}, {documented_policy.required_scope})"
            )
            for endpoint, actual_policy, documented_policy in policy_mismatches
        )
        error_messages.append(f"Policy mismatches in {source_name}: {mismatch_text}")

    if stale_documented_endpoints:
        stale_text = ", ".join(_format_endpoint(endpoint) for endpoint in stale_documented_endpoints)
        error_messages.append(f"Stale documented protected endpoints in {source_name}: {stale_text}")

    assert not error_messages, "\n".join(error_messages)


def _assert_endpoint_read_access_contract(
    actual_read_policy: dict[EndpointKey, ReadAccessPolicyRow],
    documented_read_policy: dict[EndpointKey, ReadAccessPolicyRow],
    *,
    source_name: str,
) -> None:
    missing_endpoints = sorted(endpoint for endpoint in actual_read_policy if endpoint not in documented_read_policy)
    policy_mismatches = sorted(
        (
            endpoint,
            actual_read_policy[endpoint],
            documented_read_policy[endpoint],
        )
        for endpoint in actual_read_policy
        if endpoint in documented_read_policy and documented_read_policy[endpoint] != actual_read_policy[endpoint]
    )
    stale_documented_endpoints = sorted(
        endpoint for endpoint in documented_read_policy if endpoint not in actual_read_policy
    )

    error_messages: list[str] = []
    if missing_endpoints:
        missing_text = ", ".join(_format_endpoint(endpoint) for endpoint in missing_endpoints)
        error_messages.append(f"Missing read endpoint policy rows in {source_name}: {missing_text}")

    if policy_mismatches:
        mismatch_text = ", ".join(
            (
                f"{_format_endpoint(endpoint)} expected ({actual_row.access_level}, {actual_row.permission_id}) "
                f"documented ({documented_row.access_level}, {documented_row.permission_id})"
            )
            for endpoint, actual_row, documented_row in policy_mismatches
        )
        error_messages.append(f"Read-access policy mismatches in {source_name}: {mismatch_text}")

    if stale_documented_endpoints:
        stale_text = ", ".join(_format_endpoint(endpoint) for endpoint in stale_documented_endpoints)
        error_messages.append(f"Stale documented read endpoint policies in {source_name}: {stale_text}")

    assert not error_messages, "\n".join(error_messages)


def test_authorization_matrix_matches_protected_router_endpoints() -> None:
    actual_protected_endpoints = _collect_protected_endpoints_from_routes()
    documented_protected_endpoints = _parse_authorization_matrix_inventory(AUTHORIZATION_MATRIX_PATH)

    _assert_endpoint_permission_contract(
        actual_protected_endpoints,
        documented_protected_endpoints,
        source_name=AUTHORIZATION_MATRIX_PATH.name,
    )


def test_read_access_catalog_matches_router_endpoints() -> None:
    actual_read_policy = _collect_read_endpoint_policies_from_routes()
    catalog_read_policy = _collect_read_endpoint_policies_from_catalog()

    _assert_endpoint_read_access_contract(
        actual_read_policy,
        catalog_read_policy,
        source_name="READ_ACCESS_POLICY_CATALOG",
    )


def test_authorization_matrix_documents_read_access_policy() -> None:
    actual_read_policy = _collect_read_endpoint_policies_from_routes()
    documented_read_policy = _parse_read_access_policy_section(
        AUTHORIZATION_MATRIX_PATH,
        heading="Read Endpoint Access Policy",
    )

    _assert_endpoint_read_access_contract(
        actual_read_policy,
        documented_read_policy,
        source_name=AUTHORIZATION_MATRIX_PATH.name,
    )


def test_api_endpoints_document_protected_router_permissions() -> None:
    actual_protected_endpoints = _collect_protected_endpoints_from_routes()
    endpoint_summary = _parse_api_endpoint_summary(API_ENDPOINTS_PATH)
    actual_protected_endpoint_permissions = {
        endpoint: policy.permission_id for endpoint, policy in actual_protected_endpoints.items()
    }

    missing_endpoints = sorted(
        endpoint for endpoint in actual_protected_endpoint_permissions if endpoint not in endpoint_summary
    )
    auth_mismatches = sorted(
        endpoint
        for endpoint in actual_protected_endpoint_permissions
        if endpoint in endpoint_summary and not endpoint_summary[endpoint].auth_required
    )
    permission_mismatches = sorted(
        (
            endpoint,
            actual_protected_endpoint_permissions[endpoint],
            endpoint_summary[endpoint].permission_id,
        )
        for endpoint in actual_protected_endpoint_permissions
        if endpoint in endpoint_summary
        and endpoint_summary[endpoint].permission_id != actual_protected_endpoint_permissions[endpoint]
    )

    documented_protected_endpoints = {
        endpoint: row.permission_id for endpoint, row in endpoint_summary.items() if row.permission_id is not None
    }
    stale_documented_endpoints = sorted(
        endpoint for endpoint in documented_protected_endpoints if endpoint not in actual_protected_endpoint_permissions
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


def test_api_endpoints_documents_read_access_classification() -> None:
    actual_read_policy = _collect_read_endpoint_policies_from_routes()
    documented_read_policy = _parse_read_access_policy_section(
        API_ENDPOINTS_PATH,
        heading="Read Access Classification",
    )

    _assert_endpoint_read_access_contract(
        actual_read_policy,
        documented_read_policy,
        source_name=API_ENDPOINTS_PATH.name,
    )
