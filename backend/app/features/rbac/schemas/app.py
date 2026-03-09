from pydantic import Field

from app.core.authorization import PermissionScope
from app.core.common.schema import ApplicationSchema


class CreateRoleCommand(ApplicationSchema):
    name: str


class UpdateRoleCommand(ApplicationSchema):
    name: str


class SetRolePermissionCommand(ApplicationSchema):
    scope: str = PermissionScope.ANY


class PermissionResult(ApplicationSchema):
    id: str
    name: str


class RolePermissionResult(ApplicationSchema):
    id: str
    name: str
    scope: str


class RoleResult(ApplicationSchema):
    id: int
    name: str
    permissions: list[RolePermissionResult] = Field(default_factory=list)
    parent_role_ids: list[int] = Field(default_factory=list)


class UserRoleAssignmentResult(ApplicationSchema):
    user_id: int
    role_id: int


class AssignedRoleResult(ApplicationSchema):
    id: int
    name: str


class AssignedUserResult(ApplicationSchema):
    id: int
    username: str
    disabled: bool


class AdminUserResult(ApplicationSchema):
    id: int
    username: str
    disabled: bool
    role_ids: list[int] = Field(default_factory=list)


class CreateAdminUserCommand(ApplicationSchema):
    username: str
    password: str
    role_ids: list[int] = Field(default_factory=list)


class UpdateAdminUserCommand(ApplicationSchema):
    username: str | None = None
    current_password: str | None = None
    new_password: str | None = None
    disabled: bool | None = None
    role_ids: list[int] | None = None
