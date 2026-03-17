import { ApiContractError } from "@/shared/api/contracts";
import {
  parseAssignedRoleList,
  parseAssignedUserList,
  parseAdminUser,
  parseAdminUserList,
  parseRbacPermissionList,
  parseRbacRole,
  parseRbacRolePermission,
  parseUserRoleAssignment,
} from "@/shared/rbac/contracts";

describe("rbac contracts", () => {
  it("parses admin user payload", () => {
    expect(
      parseAdminUser({
        id: 3,
        username: "ops_user",
        disabled: false,
        role_ids: [1, 2],
      }),
    ).toEqual({
      id: 3,
      username: "ops_user",
      disabled: false,
      role_ids: [1, 2],
    });
  });

  it("rejects invalid role_ids payload for admin user", () => {
    expect(() =>
      parseAdminUser({
        id: 3,
        username: "ops_user",
        disabled: false,
        role_ids: ["1"],
      }),
    ).toThrowError(
      new ApiContractError("AdminUser: field 'role_ids[0]' must be number, received string"),
    );
  });

  it("parses role payload with permissions and parent role ids", () => {
    expect(
      parseRbacRole({
        id: 1,
        name: "admin_role",
        permissions: [
          {
            id: "users:manage",
            name: "Manage users",
            scope: "any",
          },
        ],
        parent_role_ids: [2],
      }),
    ).toEqual({
      id: 1,
      name: "admin_role",
      permissions: [
        {
          id: "users:manage",
          name: "Manage users",
          scope: "any",
        },
      ],
      parent_role_ids: [2],
    });
  });

  it("parses role permission assignment payload", () => {
    expect(
      parseRbacRolePermission({
        id: "role_permissions:manage",
        name: "Manage role permissions",
        scope: "tenant",
      }),
    ).toEqual({
      id: "role_permissions:manage",
      name: "Manage role permissions",
      scope: "tenant",
    });
  });

  it("rejects unsupported permission scopes", () => {
    expect(() =>
      parseRbacRolePermission({
        id: "role_permissions:manage",
        name: "Manage role permissions",
        scope: "team",
      }),
    ).toThrowError(
      new ApiContractError("RbacRolePermission: field 'scope' must be one of own, tenant, any, received 'team'"),
    );
  });

  it("parses role and user lists", () => {
    expect(
      parseAdminUserList([
        {
          id: 1,
          username: "admin",
          disabled: false,
          role_ids: [1],
        },
      ]),
    ).toHaveLength(1);

    expect(
      parseRbacPermissionList([
        {
          id: "users:manage",
          name: "Manage users",
        },
      ]),
    ).toHaveLength(1);
  });

  it("parses direct assignment payloads", () => {
    expect(
      parseAssignedRoleList([
        {
          id: 2,
          name: "reader_role",
        },
      ]),
    ).toEqual([
      {
        id: 2,
        name: "reader_role",
      },
    ]);

    expect(
      parseAssignedUserList([
        {
          id: 3,
          username: "reader_user",
          disabled: false,
        },
      ]),
    ).toEqual([
      {
        id: 3,
        username: "reader_user",
        disabled: false,
      },
    ]);

    expect(
      parseUserRoleAssignment({
        user_id: 3,
        role_id: 2,
      }),
    ).toEqual({
      user_id: 3,
      role_id: 2,
    });
  });
});
