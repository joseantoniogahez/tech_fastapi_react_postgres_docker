import {
  ApiContractError,
  expectBooleanField,
  expectNumberField,
  expectRecord,
  expectStringField,
} from "@/shared/api/contracts";

const describeType = (value: unknown): string => {
  if (value === null) {
    return "null";
  }
  if (Array.isArray(value)) {
    return "array";
  }
  return typeof value;
};

const expectArrayField = (record: Record<string, unknown>, field: string, context: string): unknown[] => {
  if (!(field in record)) {
    throw new ApiContractError(`${context}: missing required field '${field}'`);
  }

  const value = record[field];
  if (!Array.isArray(value)) {
    throw new ApiContractError(`${context}: field '${field}' must be array, received ${describeType(value)}`);
  }

  return value;
};

const expectNumberArrayField = (record: Record<string, unknown>, field: string, context: string): number[] => {
  const values = expectArrayField(record, field, context);
  return values.map((value, index) => {
    if (typeof value !== "number" || Number.isNaN(value)) {
      throw new ApiContractError(
        `${context}: field '${field}[${index}]' must be number, received ${describeType(value)}`,
      );
    }
    return value;
  });
};

const expectRecordArray = (payload: unknown, context: string): Record<string, unknown>[] => {
  if (!Array.isArray(payload)) {
    throw new ApiContractError(`${context}: expected array payload, received ${describeType(payload)}`);
  }

  return payload.map((item, index) => expectRecord(item, `${context}[${index}]`));
};

export const RBAC_PERMISSION_SCOPES = ["own", "tenant", "any"] as const;
export type RbacPermissionScope = (typeof RBAC_PERMISSION_SCOPES)[number];

export const isRbacPermissionScope = (value: string): value is RbacPermissionScope =>
  (RBAC_PERMISSION_SCOPES as readonly string[]).includes(value);

const expectPermissionScopeField = (
  record: Record<string, unknown>,
  field: string,
  context: string,
): RbacPermissionScope => {
  const value = expectStringField(record, field, context, { minLength: 1 });
  if (!isRbacPermissionScope(value)) {
    throw new ApiContractError(
      `${context}: field '${field}' must be one of ${RBAC_PERMISSION_SCOPES.join(", ")}, received '${value}'`,
    );
  }
  return value;
};

export interface RbacPermission {
  id: string;
  name: string;
}

export interface RbacRolePermission extends RbacPermission {
  scope: RbacPermissionScope;
}

export interface RbacRole {
  id: number;
  name: string;
  permissions: RbacRolePermission[];
  parent_role_ids: number[];
}

export interface AdminUser {
  id: number;
  username: string;
  disabled: boolean;
  role_ids: number[];
}

export interface AssignedRole {
  id: number;
  name: string;
}

export interface AssignedUser {
  id: number;
  username: string;
  disabled: boolean;
}

export interface UserRoleAssignment {
  user_id: number;
  role_id: number;
}

export const parseRbacPermission = (payload: unknown): RbacPermission => {
  const context = "RbacPermission";
  const record = expectRecord(payload, context);

  return {
    id: expectStringField(record, "id", context, { minLength: 1 }),
    name: expectStringField(record, "name", context, { minLength: 1 }),
  };
};

export const parseRbacPermissionList = (payload: unknown): RbacPermission[] =>
  expectRecordArray(payload, "RbacPermissionList").map((item) => parseRbacPermission(item));

export const parseRbacRolePermission = (payload: unknown): RbacRolePermission => {
  const context = "RbacRolePermission";
  const record = expectRecord(payload, context);

  return {
    id: expectStringField(record, "id", context, { minLength: 1 }),
    name: expectStringField(record, "name", context, { minLength: 1 }),
    scope: expectPermissionScopeField(record, "scope", context),
  };
};

export const parseRbacRole = (payload: unknown): RbacRole => {
  const context = "RbacRole";
  const record = expectRecord(payload, context);

  return {
    id: expectNumberField(record, "id", context),
    name: expectStringField(record, "name", context, { minLength: 1 }),
    permissions: expectArrayField(record, "permissions", context).map((item, index) =>
      parseRbacRolePermission(expectRecord(item, `${context}.permissions[${index}]`)),
    ),
    parent_role_ids: expectNumberArrayField(record, "parent_role_ids", context),
  };
};

export const parseRbacRoleList = (payload: unknown): RbacRole[] =>
  expectRecordArray(payload, "RbacRoleList").map((item) => parseRbacRole(item));

export const parseAdminUser = (payload: unknown): AdminUser => {
  const context = "AdminUser";
  const record = expectRecord(payload, context);

  return {
    id: expectNumberField(record, "id", context),
    username: expectStringField(record, "username", context, { minLength: 1 }),
    disabled: expectBooleanField(record, "disabled", context),
    role_ids: expectNumberArrayField(record, "role_ids", context),
  };
};

export const parseAdminUserList = (payload: unknown): AdminUser[] =>
  expectRecordArray(payload, "AdminUserList").map((item) => parseAdminUser(item));

export const parseAssignedRole = (payload: unknown): AssignedRole => {
  const context = "AssignedRole";
  const record = expectRecord(payload, context);

  return {
    id: expectNumberField(record, "id", context),
    name: expectStringField(record, "name", context, { minLength: 1 }),
  };
};

export const parseAssignedRoleList = (payload: unknown): AssignedRole[] =>
  expectRecordArray(payload, "AssignedRoleList").map((item) => parseAssignedRole(item));

export const parseAssignedUser = (payload: unknown): AssignedUser => {
  const context = "AssignedUser";
  const record = expectRecord(payload, context);

  return {
    id: expectNumberField(record, "id", context),
    username: expectStringField(record, "username", context, { minLength: 1 }),
    disabled: expectBooleanField(record, "disabled", context),
  };
};

export const parseAssignedUserList = (payload: unknown): AssignedUser[] =>
  expectRecordArray(payload, "AssignedUserList").map((item) => parseAssignedUser(item));

export const parseUserRoleAssignment = (payload: unknown): UserRoleAssignment => {
  const context = "UserRoleAssignment";
  const record = expectRecord(payload, context);

  return {
    user_id: expectNumberField(record, "user_id", context),
    role_id: expectNumberField(record, "role_id", context),
  };
};
