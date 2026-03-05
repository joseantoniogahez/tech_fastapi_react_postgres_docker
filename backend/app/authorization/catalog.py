from app.authorization.policies import validate_permission_catalog, validate_read_access_policy_catalog
from app.authorization.types import PermissionDefinition, ReadAccessLevel, ReadAccessPolicyDefinition

PERMISSION_CATALOG: tuple[PermissionDefinition, ...] = (
    PermissionDefinition(resource="books", action="create", name="Create books"),
    PermissionDefinition(resource="books", action="update", name="Update books"),
    PermissionDefinition(resource="books", action="delete", name="Delete books"),
    PermissionDefinition(resource="roles", action="manage", name="Manage roles"),
    PermissionDefinition(resource="role_permissions", action="manage", name="Manage role permissions"),
    PermissionDefinition(resource="user_roles", action="manage", name="Manage user role assignments"),
)

validate_permission_catalog(PERMISSION_CATALOG)

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
    ROLE_MANAGE = _PERMISSION_IDS_BY_RESOURCE_ACTION[("roles", "manage")]
    ROLE_PERMISSION_MANAGE = _PERMISSION_IDS_BY_RESOURCE_ACTION[("role_permissions", "manage")]
    USER_ROLE_MANAGE = _PERMISSION_IDS_BY_RESOURCE_ACTION[("user_roles", "manage")]


READ_ACCESS_POLICY_CATALOG: tuple[ReadAccessPolicyDefinition, ...] = (
    ReadAccessPolicyDefinition(method="GET", path="/v1/health", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(method="GET", path="/v1/users/me", access_level=ReadAccessLevel.AUTHENTICATED),
    ReadAccessPolicyDefinition(method="GET", path="/v1/authors/", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(method="GET", path="/v1/books/", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(method="GET", path="/v1/books/published", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(method="GET", path="/v1/books/{book_id}", access_level=ReadAccessLevel.PUBLIC),
    ReadAccessPolicyDefinition(
        method="GET",
        path="/v1/rbac/roles",
        access_level=ReadAccessLevel.PERMISSION,
        permission_id=PermissionId.ROLE_MANAGE,
    ),
    ReadAccessPolicyDefinition(
        method="GET",
        path="/v1/rbac/permissions",
        access_level=ReadAccessLevel.PERMISSION,
        permission_id=PermissionId.ROLE_PERMISSION_MANAGE,
    ),
)

validate_read_access_policy_catalog(
    READ_ACCESS_POLICY_CATALOG,
    permission_catalog_by_id=PERMISSION_CATALOG_BY_ID,
)

READ_ACCESS_POLICY_BY_ENDPOINT: dict[tuple[str, str], ReadAccessPolicyDefinition] = {
    policy.endpoint: policy for policy in READ_ACCESS_POLICY_CATALOG
}
