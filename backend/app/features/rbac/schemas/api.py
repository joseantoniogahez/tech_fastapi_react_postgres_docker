from pydantic import ConfigDict, Field

from app.core.authorization import PermissionScope
from app.core.common.schema import ApiSchema


class RBACPermission(ApiSchema):
    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class RBACRolePermission(RBACPermission):
    scope: str = Field(min_length=1, max_length=20)


class RBACRole(ApiSchema):
    id: int
    name: str = Field(min_length=1, max_length=100)
    permissions: list[RBACRolePermission] = Field(default_factory=list)


class CreateRoleRequest(ApiSchema):
    name: str = Field(min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateRoleRequest(CreateRoleRequest):
    pass


class SetRolePermissionRequest(ApiSchema):
    scope: str = Field(default=PermissionScope.ANY, min_length=1, max_length=20)

    model_config = ConfigDict(str_strip_whitespace=True)


class UserRoleAssignmentResponse(ApiSchema):
    user_id: int
    role_id: int
