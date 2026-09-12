import {
  MUTATION_POLICY_MATRIX,
  authLoginMutationPolicy,
  authLogoutMutationPolicy,
  defaultMutationPolicy,
} from "@/app/mutation-policy";

describe("mutation policy", () => {
  it("disables inherited automatic retry for every default mutation failure", () => {
    expect(MUTATION_POLICY_MATRIX.defaultMutation.retry).toBe(false);
    expect(defaultMutationPolicy.retry).toBe(false);
  });

  it("keeps auth mutation policies as explicit no-retry contracts", () => {
    expect(MUTATION_POLICY_MATRIX.authLoginMutation.retry).toBe(false);
    expect(MUTATION_POLICY_MATRIX.authLogoutMutation.retry).toBe(false);
    expect(authLoginMutationPolicy.retry).toBe(false);
    expect(authLogoutMutationPolicy.retry).toBe(false);
  });
});
