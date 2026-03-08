import { ES_MESSAGES, t, type UiTextKey } from "@/shared/i18n/ui-text";

const MOJIBAKE_PATTERN = new RegExp(String.raw`\u00C3|\uFFFD`);

const REQUIRED_UI_KEYS: readonly UiTextKey[] = [
  "auth.login.badge",
  "auth.login.error.generic",
  "auth.login.fields.password",
  "auth.login.fields.username",
  "auth.login.footer.backToLanding",
  "auth.login.footer.firstTime",
  "auth.login.submit.default",
  "auth.login.submit.pending",
  "auth.login.subtitle",
  "auth.login.title",
  "auth.login.validating.title",
  "landing.badge.portal",
  "landing.cta.login",
  "landing.loading.title",
  "landing.subtitle",
  "landing.title",
  "routing.error.body",
  "routing.error.title",
  "routing.notFound.body",
  "routing.notFound.title",
  "routing.protected.error.body",
  "routing.protected.error.title",
  "routing.protected.validating.body",
  "routing.protected.validating.title",
  "shared.centeredMessage.stateLabel",
  "welcome.badge",
  "welcome.greeting",
  "welcome.logout",
  "welcome.logout.pending",
  "welcome.noSession.body",
  "welcome.noSession.title",
  "welcome.sessionActive.body",
];

describe("ui text catalog integrity", () => {
  it("contains all required UI keys", () => {
    for (const key of REQUIRED_UI_KEYS) {
      expect(ES_MESSAGES[key]).toBeDefined();
    }
  });

  it("contains non-empty message values", () => {
    for (const [key, value] of Object.entries(ES_MESSAGES)) {
      expect(value.trim(), `message '${key}' must not be empty`).not.toBe("");
    }
  });

  it("does not contain mojibake sequences", () => {
    for (const [key, value] of Object.entries(ES_MESSAGES)) {
      expect(MOJIBAKE_PATTERN.test(value), `message '${key}' contains mojibake: '${value}'`).toBe(false);
    }
  });

  it("resolves every key through the translation function", () => {
    for (const key of Object.keys(ES_MESSAGES) as UiTextKey[]) {
      expect(() => t(key)).not.toThrow();
      expect(typeof t(key)).toBe("string");
    }
  });
});
