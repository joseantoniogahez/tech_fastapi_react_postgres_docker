import type { UiTextKey } from "@/shared/i18n/ui-text";

const USERNAME_PATTERN = /^[a-z0-9_.-]+$/;
const LOWERCASE_PATTERN = /[a-z]/;
const UPPERCASE_PATTERN = /[A-Z]/;
const NUMBER_PATTERN = /[0-9]/;

export const normalizeUsername = (value: string): string => value.trim().toLowerCase();

export const isNormalizedUsernameValid = (value: string): boolean => USERNAME_PATTERN.test(normalizeUsername(value));

export const getPasswordPolicyViolationKeys = (password: string, username: string): UiTextKey[] => {
  const normalizedUsername = normalizeUsername(username);
  const normalizedPassword = password.toLowerCase();
  const violations: UiTextKey[] = [];

  if (password.length < 8) {
    violations.push("auth.validation.password.length");
  }
  if (!LOWERCASE_PATTERN.test(password)) {
    violations.push("auth.validation.password.lowercase");
  }
  if (!UPPERCASE_PATTERN.test(password)) {
    violations.push("auth.validation.password.uppercase");
  }
  if (!NUMBER_PATTERN.test(password)) {
    violations.push("auth.validation.password.number");
  }
  if (normalizedUsername.length > 0 && normalizedPassword.includes(normalizedUsername)) {
    violations.push("auth.validation.password.containsUsername");
  }

  return violations;
};
