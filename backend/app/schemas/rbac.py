from pydantic import BaseModel, ConfigDict, Field

from app.const.permission import PermissionScope


class RBACPermission(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class RBACRolePermission(RBACPermission):
    scope: str = Field(min_length=1, max_length=20)


class RBACRole(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)
    permissions: list[RBACRolePermission] = Field(default_factory=list)


class CreateRole(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    model_config = ConfigDict(str_strip_whitespace=True)


class UpdateRole(CreateRole):
    pass


class SetRolePermission(BaseModel):
    scope: str = Field(default=PermissionScope.ANY, min_length=1, max_length=20)

    model_config = ConfigDict(str_strip_whitespace=True)


class UserRoleAssignment(BaseModel):
    user_id: int
    role_id: int
