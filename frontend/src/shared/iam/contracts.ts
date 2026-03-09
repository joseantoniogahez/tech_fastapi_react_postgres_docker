export const IAM_PERMISSION = {
  ROLE_PERMISSIONS_MANAGE: "role_permissions:manage",
  ROLES_MANAGE: "roles:manage",
  USER_ROLES_MANAGE: "user_roles:manage",
  USERS_MANAGE: "users:manage",
} as const;

export type IamPermissionId = (typeof IAM_PERMISSION)[keyof typeof IAM_PERMISSION];
