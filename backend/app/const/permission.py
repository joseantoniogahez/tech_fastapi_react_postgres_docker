import re
from dataclasses import dataclass
from typing import Final

PERMISSION_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class PermissionDefinition:
    resource: str
    action: str
    name: str

    @property
    def id(self) -> str:
        return build_permission_id(resource=self.resource, action=self.action)


def build_permission_id(*, resource: str, action: str) -> str:
    permission_id = f"{resource}:{action}"
    if PERMISSION_ID_PATTERN.fullmatch(permission_id) is None:
        raise ValueError(
            f"Invalid permission id '{permission_id}'. "
            "Expected '<resource>:<action>' with lowercase letters, numbers, and underscores."
        )
    return permission_id


class ReadAccessLevel:
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    PERMISSION = "permission"


READ_ACCESS_LEVELS: Final[frozenset[str]] = frozenset(
    {
        ReadAccessLevel.PUBLIC,
        ReadAccessLevel.AUTHENTICATED,
        ReadAccessLevel.PERMISSION,
    }
)


@dataclass(frozen=True)
class ReadAccessPolicyDefinition:
    method: str
    path: str
    access_level: str
    permission_id: str | None = None

    @property
    def endpoint(self) -> tuple[str, str]:
        return (self.method, self.path)


PERMISSION_CATALOG: tuple[PermissionDefinition, ...] = (
    PermissionDefinition(resource="books", action="create", name="Create books"),
    PermissionDefinition(resource="books", action="update", name="Update books"),
    PermissionDefinition(resource="books", action="delete", name="Delete books"),
)


def _validate_permission_catalog(catalog: tuple[PermissionDefinition, ...]) -> None:
    duplicated_ids: set[str] = set()
    seen_ids: set[str] = set()

    for permission in catalog:
        permission_id = permission.id
        if permission_id in seen_ids:
            duplicated_ids.add(permission_id)
            continue
        seen_ids.add(permission_id)

    if duplicated_ids:
        duplicated_ids_list = ", ".join(sorted(duplicated_ids))
        raise ValueError(f"Duplicate permission ids in PERMISSION_CATALOG: {duplicated_ids_list}")


_validate_permission_catalog(PERMISSION_CATALOG)

PERMISSION_CATALOG_BY_ID: dict[str, PermissionDefinition] = {
    permission.id: permission for permission in PERMISSION_CATALOG
}
PERMISSION_IDS: tuple[str, ...] = tuple(PERMISSION_CATALOG_BY_ID.keys())
PERMISSION_SPECS: tuple[tuple[str, str], ...] = tuple(
    (permission.id, permission.name) for permission in PERMISSION_CATALOG
)

_PERMISSION_IDS_BY_RESOURCE_ACTION: dict[tuple[str, str], str] = {
    (permission.resource, permission.action): permission.id for permission in PERMISSION_CATALOG
}


class PermissionId:
    BOOK_CREATE = _PERMISSION_IDS_BY_RESOURCE_ACTION[("books", "create")]
    BOOK_UPDATE = _PERMISSION_IDS_BY_RESOURCE_ACTION[("books", "update")]
    BOOK_DELETE = _PERMISSION_IDS_BY_RESOURCE_ACTION[("books", "delete")]


READ_ACCESS_POLICY_CATALOG: tuple[ReadAccessPolicyDefinition, ...] = (
    ReadAccessPolicyDefinition(method="GET", path="/health", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(method="GET", path="/users/me", access_level=ReadAccessLevel.AUTHENTICATED),
    ReadAccessPolicyDefinition(method="GET", path="/authors/", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(method="GET", path="/books/", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(method="GET", path="/books/published", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(method="GET", path="/books/{id}", access_level=ReadAccessLevel.PUBLIC),
)


def _validate_read_access_policy_structure(policy: ReadAccessPolicyDefinition) -> None:
    if policy.method != "GET":
        raise ValueError(f"Invalid read-access method '{policy.method}' for endpoint {policy.method} {policy.path}")

    if not policy.path.startswith("/"):
        raise ValueError(f"Invalid read-access path '{policy.path}'. Paths must start with '/'.")

    if policy.access_level not in READ_ACCESS_LEVELS:
        raise ValueError(
            f"Invalid read-access level '{policy.access_level}' for endpoint {policy.method} {policy.path}. "
            f"Expected one of {sorted(READ_ACCESS_LEVELS)}."
        )


def _validate_read_access_policy_permission_link(policy: ReadAccessPolicyDefinition) -> None:
    permission_id = policy.permission_id
    if policy.access_level == ReadAccessLevel.PERMISSION:
        if permission_id is None:
            raise ValueError(
                "Permission-based read-access policies require permission_id for endpoint "
                f"{policy.method} {policy.path}."
            )
        if permission_id not in PERMISSION_CATALOG_BY_ID:
            raise ValueError(
                f"Unknown permission id '{permission_id}' in read-access policy "
                f"for endpoint {policy.method} {policy.path}."
            )
        return

    if permission_id is not None:
        raise ValueError(
            f"Non-permission read-access policy for endpoint {policy.method} {policy.path} "
            f"must not define permission_id '{permission_id}'."
        )


def _validate_read_access_policy_catalog(catalog: tuple[ReadAccessPolicyDefinition, ...]) -> None:
    duplicated_endpoints: set[tuple[str, str]] = set()
    seen_endpoints: set[tuple[str, str]] = set()

    for policy in catalog:
        endpoint = policy.endpoint
        if endpoint in seen_endpoints:
            duplicated_endpoints.add(endpoint)
        else:
            seen_endpoints.add(endpoint)

        _validate_read_access_policy_structure(policy)
        _validate_read_access_policy_permission_link(policy)

    if duplicated_endpoints:
        duplicated_endpoints_list = ", ".join(f"{method} {path}" for method, path in sorted(duplicated_endpoints))
        raise ValueError(f"Duplicate endpoints in READ_ACCESS_POLICY_CATALOG: {duplicated_endpoints_list}")


_validate_read_access_policy_catalog(READ_ACCESS_POLICY_CATALOG)

READ_ACCESS_POLICY_BY_ENDPOINT: dict[tuple[str, str], ReadAccessPolicyDefinition] = {
    policy.endpoint: policy for policy in READ_ACCESS_POLICY_CATALOG
}
