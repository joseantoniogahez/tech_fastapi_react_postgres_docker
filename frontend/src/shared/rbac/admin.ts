import {
  apiNoContentRequest,
  apiRequest,
  type NoContentRequestOptions,
  type RequestOptions,
} from "@/shared/api/http";
import {
  parseAssignedRoleList,
  parseAssignedUserList,
  parseAdminUser,
  parseAdminUserList,
  parseRbacPermissionList,
  parseRbacRole,
  parseRbacRoleList,
  parseRbacRolePermission,
  parseUserRoleAssignment,
  type AssignedRole,
  type AssignedUser,
  type AdminUser,
  type RbacPermission,
  type RbacPermissionScope,
  type RbacRole,
  type RbacRolePermission,
  type UserRoleAssignment,
} from "@/shared/rbac/contracts";

export interface CreateAdminUserPayload {
  username: string;
  password: string;
  role_ids?: number[];
}

export interface UpdateAdminUserPayload {
  username?: string;
  current_password?: string;
  new_password?: string;
  disabled?: boolean;
  role_ids?: number[];
}

export interface UpsertRolePayload {
  name: string;
}

export interface AssignRolePermissionPayload {
  scope: RbacPermissionScope;
}

export const RBAC_USERS_ENDPOINT_PATH = "/rbac/users";
export const RBAC_ROLES_ENDPOINT_PATH = "/rbac/roles";
export const RBAC_PERMISSIONS_ENDPOINT_PATH = "/rbac/permissions";
export const RBAC_USER_ENDPOINT_PATH_TEMPLATE = `${RBAC_USERS_ENDPOINT_PATH}/{user_id}`;
export const RBAC_ROLE_ENDPOINT_PATH_TEMPLATE = `${RBAC_ROLES_ENDPOINT_PATH}/{role_id}`;
export const RBAC_USER_ROLES_ENDPOINT_PATH_TEMPLATE = `${RBAC_USER_ENDPOINT_PATH_TEMPLATE}/roles`;
export const RBAC_ROLE_USERS_ENDPOINT_PATH_TEMPLATE = `${RBAC_ROLE_ENDPOINT_PATH_TEMPLATE}/users`;
export const RBAC_USER_ROLE_ENDPOINT_PATH_TEMPLATE =
  `${RBAC_USER_ROLES_ENDPOINT_PATH_TEMPLATE}/{role_id}`;
export const RBAC_ROLE_INHERITANCE_ENDPOINT_PATH_TEMPLATE =
  `${RBAC_ROLE_ENDPOINT_PATH_TEMPLATE}/inherits/{parent_role_id}`;
export const RBAC_ROLE_PERMISSION_ENDPOINT_PATH_TEMPLATE =
  `${RBAC_ROLE_ENDPOINT_PATH_TEMPLATE}/permissions/{permission_id}`;

export const buildRbacUserPath = (userId: number): string => `${RBAC_USERS_ENDPOINT_PATH}/${userId}`;
export const buildRbacRolePath = (roleId: number): string => `${RBAC_ROLES_ENDPOINT_PATH}/${roleId}`;
export const buildRbacUserRolesPath = (userId: number): string => `${buildRbacUserPath(userId)}/roles`;
export const buildRbacRoleUsersPath = (roleId: number): string => `${buildRbacRolePath(roleId)}/users`;
export const buildRbacUserRolePath = (userId: number, roleId: number): string =>
  `${buildRbacUserPath(userId)}/roles/${roleId}`;
export const buildRbacRoleInheritancePath = (roleId: number, parentRoleId: number): string =>
  `${buildRbacRolePath(roleId)}/inherits/${parentRoleId}`;
export const buildRbacRolePermissionPath = (roleId: number, permissionId: string): string =>
  `${buildRbacRolePath(roleId)}/permissions/${encodeURIComponent(permissionId)}`;

const JSON_HEADERS = {
  "Content-Type": "application/json",
} as const;

const dynamicApiRequest = <T>(
  path: string,
  diagnosticPath: string,
  options: Omit<RequestOptions<T>, "diagnosticPath">,
): Promise<T> => apiRequest<T>(path, { ...options, diagnosticPath });

const dynamicApiNoContentRequest = (
  path: string,
  diagnosticPath: string,
  options: Omit<NoContentRequestOptions, "diagnosticPath"> = {},
): Promise<void> => apiNoContentRequest(path, { ...options, diagnosticPath });

export const readAdminUsers = (): Promise<AdminUser[]> =>
  apiRequest<AdminUser[]>(RBAC_USERS_ENDPOINT_PATH, {
    parse: parseAdminUserList,
  });

export const readAdminUser = (userId: number): Promise<AdminUser> =>
  dynamicApiRequest<AdminUser>(buildRbacUserPath(userId), RBAC_USER_ENDPOINT_PATH_TEMPLATE, {
    parse: parseAdminUser,
  });

export const readRbacUserRoles = (userId: number): Promise<AssignedRole[]> =>
  dynamicApiRequest<AssignedRole[]>(buildRbacUserRolesPath(userId), RBAC_USER_ROLES_ENDPOINT_PATH_TEMPLATE, {
    parse: parseAssignedRoleList,
  });

export const readRbacRoleUsers = (roleId: number): Promise<AssignedUser[]> =>
  dynamicApiRequest<AssignedUser[]>(buildRbacRoleUsersPath(roleId), RBAC_ROLE_USERS_ENDPOINT_PATH_TEMPLATE, {
    parse: parseAssignedUserList,
  });

export const createAdminUser = (payload: CreateAdminUserPayload): Promise<AdminUser> =>
  apiRequest<AdminUser>(RBAC_USERS_ENDPOINT_PATH, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseAdminUser,
  });

export const updateAdminUser = (userId: number, payload: UpdateAdminUserPayload): Promise<AdminUser> =>
  dynamicApiRequest<AdminUser>(buildRbacUserPath(userId), RBAC_USER_ENDPOINT_PATH_TEMPLATE, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseAdminUser,
  });

export const softDeleteAdminUser = (userId: number): Promise<void> =>
  dynamicApiNoContentRequest(buildRbacUserPath(userId), RBAC_USER_ENDPOINT_PATH_TEMPLATE, {
    method: "DELETE",
  });

export const assignRbacUserRole = (userId: number, roleId: number): Promise<UserRoleAssignment> =>
  dynamicApiRequest<UserRoleAssignment>(buildRbacUserRolePath(userId, roleId), RBAC_USER_ROLE_ENDPOINT_PATH_TEMPLATE, {
    method: "PUT",
    parse: parseUserRoleAssignment,
  });

export const removeRbacUserRole = (userId: number, roleId: number): Promise<void> =>
  dynamicApiNoContentRequest(buildRbacUserRolePath(userId, roleId), RBAC_USER_ROLE_ENDPOINT_PATH_TEMPLATE, {
    method: "DELETE",
  });

export const readRbacRoles = (): Promise<RbacRole[]> =>
  apiRequest<RbacRole[]>(RBAC_ROLES_ENDPOINT_PATH, {
    parse: parseRbacRoleList,
  });

export const createRbacRole = (payload: UpsertRolePayload): Promise<RbacRole> =>
  apiRequest<RbacRole>(RBAC_ROLES_ENDPOINT_PATH, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseRbacRole,
  });

export const updateRbacRole = (roleId: number, payload: UpsertRolePayload): Promise<RbacRole> =>
  dynamicApiRequest<RbacRole>(buildRbacRolePath(roleId), RBAC_ROLE_ENDPOINT_PATH_TEMPLATE, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseRbacRole,
  });

export const deleteRbacRole = (roleId: number): Promise<void> =>
  dynamicApiNoContentRequest(buildRbacRolePath(roleId), RBAC_ROLE_ENDPOINT_PATH_TEMPLATE, {
    method: "DELETE",
  });

export const assignRbacRoleInheritance = (roleId: number, parentRoleId: number): Promise<void> =>
  dynamicApiNoContentRequest(buildRbacRoleInheritancePath(roleId, parentRoleId), RBAC_ROLE_INHERITANCE_ENDPOINT_PATH_TEMPLATE, {
    method: "PUT",
  });

export const removeRbacRoleInheritance = (roleId: number, parentRoleId: number): Promise<void> =>
  dynamicApiNoContentRequest(buildRbacRoleInheritancePath(roleId, parentRoleId), RBAC_ROLE_INHERITANCE_ENDPOINT_PATH_TEMPLATE, {
    method: "DELETE",
  });

export const readRbacPermissions = (): Promise<RbacPermission[]> =>
  apiRequest<RbacPermission[]>(RBAC_PERMISSIONS_ENDPOINT_PATH, {
    parse: parseRbacPermissionList,
  });

export const assignRbacRolePermission = (
  roleId: number,
  permissionId: string,
  payload: AssignRolePermissionPayload,
): Promise<RbacRolePermission> =>
  dynamicApiRequest<RbacRolePermission>(buildRbacRolePermissionPath(roleId, permissionId), RBAC_ROLE_PERMISSION_ENDPOINT_PATH_TEMPLATE, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseRbacRolePermission,
  });

export const removeRbacRolePermission = (roleId: number, permissionId: string): Promise<void> =>
  dynamicApiNoContentRequest(buildRbacRolePermissionPath(roleId, permissionId), RBAC_ROLE_PERMISSION_ENDPOINT_PATH_TEMPLATE, {
    method: "DELETE",
  });
