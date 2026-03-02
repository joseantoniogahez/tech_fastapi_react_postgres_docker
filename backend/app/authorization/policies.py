from collections.abc import Mapping

from app.authorization.types import (
    PERMISSION_SCOPE_RANK,
    PERMISSION_SCOPES,
    READ_ACCESS_LEVELS,
    PermissionDefinition,
    ReadAccessLevel,
    ReadAccessPolicyDefinition,
)


def normalize_permission_scope(scope: str) -> str:
    normalized_scope = scope.strip().lower()
    if normalized_scope not in PERMISSION_SCOPE_RANK:
        raise ValueError(f"Invalid permission scope '{scope}'. Expected one of {sorted(PERMISSION_SCOPES)}.")
    return normalized_scope


def validate_permission_catalog(catalog: tuple[PermissionDefinition, ...]) -> None:
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


def _resolve_permission_catalog_by_id(
    permission_catalog_by_id: Mapping[str, PermissionDefinition] | None,
) -> Mapping[str, PermissionDefinition]:
    if permission_catalog_by_id is not None:
        return permission_catalog_by_id

    from app.authorization.catalog import PERMISSION_CATALOG_BY_ID

    return PERMISSION_CATALOG_BY_ID


def validate_read_access_policy_structure(policy: ReadAccessPolicyDefinition) -> None:
    if policy.method != "GET":
        raise ValueError(f"Invalid read-access method '{policy.method}' for endpoint {policy.method} {policy.path}")

    if not policy.path.startswith("/"):
        raise ValueError(f"Invalid read-access path '{policy.path}'. Paths must start with '/'.")

    if policy.access_level not in READ_ACCESS_LEVELS:
        raise ValueError(
            f"Invalid read-access level '{policy.access_level}' for endpoint {policy.method} {policy.path}. "
            f"Expected one of {sorted(READ_ACCESS_LEVELS)}."
        )


def validate_read_access_policy_permission_link(
    policy: ReadAccessPolicyDefinition,
    *,
    permission_catalog_by_id: Mapping[str, PermissionDefinition] | None = None,
) -> None:
    permission_id = policy.permission_id
    catalog_by_id = _resolve_permission_catalog_by_id(permission_catalog_by_id)
    if policy.access_level == ReadAccessLevel.PERMISSION:
        if permission_id is None:
            raise ValueError(
                "Permission-based read-access policies require permission_id for endpoint "
                f"{policy.method} {policy.path}."
            )
        if permission_id not in catalog_by_id:
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


def validate_read_access_policy_catalog(
    catalog: tuple[ReadAccessPolicyDefinition, ...],
    *,
    permission_catalog_by_id: Mapping[str, PermissionDefinition] | None = None,
) -> None:
    duplicated_endpoints: set[tuple[str, str]] = set()
    seen_endpoints: set[tuple[str, str]] = set()
    catalog_by_id = _resolve_permission_catalog_by_id(permission_catalog_by_id)

    for policy in catalog:
        endpoint = policy.endpoint
        if endpoint in seen_endpoints:
            duplicated_endpoints.add(endpoint)
        else:
            seen_endpoints.add(endpoint)

        validate_read_access_policy_structure(policy)
        validate_read_access_policy_permission_link(policy, permission_catalog_by_id=catalog_by_id)

    if duplicated_endpoints:
        duplicated_endpoints_list = ", ".join(f"{method} {path}" for method, path in sorted(duplicated_endpoints))
        raise ValueError(f"Duplicate endpoints in READ_ACCESS_POLICY_CATALOG: {duplicated_endpoints_list}")
