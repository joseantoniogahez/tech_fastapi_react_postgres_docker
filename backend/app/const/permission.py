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
