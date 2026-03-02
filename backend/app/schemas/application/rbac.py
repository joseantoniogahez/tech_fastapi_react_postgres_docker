from pydantic import Field

from app.authorization import PermissionScope

from .base import ApplicationSchema


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


class UserRoleAssignmentResult(ApplicationSchema):
    user_id: int
    role_id: int
