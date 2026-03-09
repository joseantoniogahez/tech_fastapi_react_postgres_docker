import { hasAnyPermission, hasPermission, userHasAnyPermission, userHasPermission } from "@/shared/iam/api";

describe("iam helpers", () => {
  it("checks direct permission membership", () => {
    expect(hasPermission(["users:manage"], "users:manage")).toBe(true);
    expect(hasPermission(["users:manage"], "roles:manage")).toBe(false);
    expect(hasPermission(undefined, "users:manage")).toBe(false);
  });

  it("checks any-of permission membership", () => {
    expect(hasAnyPermission(["users:manage"], ["roles:manage", "users:manage"])).toBe(true);
    expect(hasAnyPermission(["users:manage"], ["roles:manage"])).toBe(false);
  });

  it("checks permissions from session user object", () => {
    const user = {
      permissions: ["role_permissions:manage"],
    };

    expect(userHasPermission(user, "role_permissions:manage")).toBe(true);
    expect(userHasPermission(user, "users:manage")).toBe(false);
    expect(userHasAnyPermission(user, ["users:manage", "role_permissions:manage"])).toBe(true);
  });
});
