import {
  getPasswordPolicyViolationKeys,
  isNormalizedUsernameValid,
  normalizeUsername,
} from "@/shared/auth/validation";

describe("auth validation helpers", () => {
  it("normalizes usernames with trim and lowercase", () => {
    expect(normalizeUsername("  Mixed.User  ")).toBe("mixed.user");
  });

  it("validates normalized usernames against the backend-safe pattern", () => {
    expect(isNormalizedUsernameValid("Valid_User-1")).toBe(true);
    expect(isNormalizedUsernameValid("invalid user!")).toBe(false);
  });

  it("returns password policy violation keys", () => {
    expect(getPasswordPolicyViolationKeys("short", "new_user")).toEqual([
      "auth.validation.password.length",
      "auth.validation.password.uppercase",
      "auth.validation.password.number",
    ]);

    expect(getPasswordPolicyViolationKeys("New_User123", "new_user")).toContain(
      "auth.validation.password.containsUsername",
    );
  });
});
