import { apiRequest } from "@/shared/api/http";
import {
  parseAdminUser,
  parseAdminUserList,
  parseRbacPermissionList,
  parseRbacRole,
  parseRbacRoleList,
  parseRbacRolePermission,
  type AdminUser,
  type RbacPermission,
  type RbacRole,
  type RbacRolePermission,
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
  scope: string;
}

export const RBAC_USERS_ENDPOINT_PATH = "/rbac/users";
export const RBAC_ROLES_ENDPOINT_PATH = "/rbac/roles";
export const RBAC_PERMISSIONS_ENDPOINT_PATH = "/rbac/permissions";

export const buildRbacUserPath = (userId: number): string => `${RBAC_USERS_ENDPOINT_PATH}/${userId}`;
export const buildRbacRolePath = (roleId: number): string => `${RBAC_ROLES_ENDPOINT_PATH}/${roleId}`;
export const buildRbacRoleInheritancePath = (roleId: number, parentRoleId: number): string =>
  `${buildRbacRolePath(roleId)}/inherits/${parentRoleId}`;
export const buildRbacRolePermissionPath = (roleId: number, permissionId: string): string =>
  `${buildRbacRolePath(roleId)}/permissions/${encodeURIComponent(permissionId)}`;

const JSON_HEADERS = {
  "Content-Type": "application/json",
} as const;

export const readAdminUsers = (): Promise<AdminUser[]> =>
  apiRequest<AdminUser[]>(RBAC_USERS_ENDPOINT_PATH, {
    parse: parseAdminUserList,
  });

export const readAdminUser = (userId: number): Promise<AdminUser> =>
  apiRequest<AdminUser>(buildRbacUserPath(userId), {
    parse: parseAdminUser,
  });

export const createAdminUser = (payload: CreateAdminUserPayload): Promise<AdminUser> =>
  apiRequest<AdminUser>(RBAC_USERS_ENDPOINT_PATH, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseAdminUser,
  });

export const updateAdminUser = (userId: number, payload: UpdateAdminUserPayload): Promise<AdminUser> =>
  apiRequest<AdminUser>(buildRbacUserPath(userId), {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseAdminUser,
  });

export const softDeleteAdminUser = (userId: number): Promise<void> =>
  apiRequest<void>(buildRbacUserPath(userId), {
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
  apiRequest<RbacRole>(buildRbacRolePath(roleId), {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseRbacRole,
  });

export const deleteRbacRole = (roleId: number): Promise<void> =>
  apiRequest<void>(buildRbacRolePath(roleId), {
    method: "DELETE",
  });

export const assignRbacRoleInheritance = (roleId: number, parentRoleId: number): Promise<void> =>
  apiRequest<void>(buildRbacRoleInheritancePath(roleId, parentRoleId), {
    method: "PUT",
  });

export const removeRbacRoleInheritance = (roleId: number, parentRoleId: number): Promise<void> =>
  apiRequest<void>(buildRbacRoleInheritancePath(roleId, parentRoleId), {
    method: "DELETE",
  });

export const readRbacPermissions = (): Promise<RbacPermission[]> =>
  apiRequest<RbacPermission[]>(RBAC_PERMISSIONS_ENDPOINT_PATH, {
    parse: parseRbacPermissionList,
  });

export const assignRbacRolePermission = (
  roleId: number,
  permissionId: string,
  payload: AssignRolePermissionPayload = { scope: "any" },
): Promise<RbacRolePermission> =>
  apiRequest<RbacRolePermission>(buildRbacRolePermissionPath(roleId, permissionId), {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
    parse: parseRbacRolePermission,
  });

export const removeRbacRolePermission = (roleId: number, permissionId: string): Promise<void> =>
  apiRequest<void>(buildRbacRolePermissionPath(roleId, permissionId), {
    method: "DELETE",
  });
