from dataclasses import dataclass
from typing import Final

from app.authorization.ids import build_permission_id


@dataclass(frozen=True)
class PermissionDefinition:
    resource: str
    action: str
    name: str

    @property
    def id(self) -> str:
        return build_permission_id(resource=self.resource, action=self.action)


class PermissionScope:
    OWN = "own"
    TENANT = "tenant"
    ANY = "any"


PERMISSION_SCOPES: Final[tuple[str, ...]] = (
    PermissionScope.OWN,
    PermissionScope.TENANT,
    PermissionScope.ANY,
)
PERMISSION_SCOPE_RANK: Final[dict[str, int]] = {
    PermissionScope.OWN: 1,
    PermissionScope.TENANT: 2,
    PermissionScope.ANY: 3,
}


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
