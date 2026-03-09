import type { AuthenticatedUser } from "@/shared/auth/session";

export const hasPermission = (permissions: readonly string[] | undefined, permissionId: string): boolean =>
  permissions?.includes(permissionId) ?? false;

export const hasAnyPermission = (
  permissions: readonly string[] | undefined,
  requiredPermissionIds: readonly string[],
): boolean => requiredPermissionIds.some((permissionId) => hasPermission(permissions, permissionId));

export const userHasPermission = (
  user: Pick<AuthenticatedUser, "permissions"> | null | undefined,
  permissionId: string,
): boolean => hasPermission(user?.permissions, permissionId);

export const userHasAnyPermission = (
  user: Pick<AuthenticatedUser, "permissions"> | null | undefined,
  requiredPermissionIds: readonly string[],
): boolean => hasAnyPermission(user?.permissions, requiredPermissionIds);
