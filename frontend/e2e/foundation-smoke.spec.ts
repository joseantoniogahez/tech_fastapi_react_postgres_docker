import { expect, test, type Page } from "@playwright/test";
import { t } from "../src/shared/i18n/ui-text";

const ACCESS_TOKEN_STORAGE_KEY = "auth.session.access_token";
const SMOKE_USERNAME = "smoke-user";

const mockUnhandledApiRequests = async (page: Page): Promise<void> => {
  await page.route("**/v1/**", (route) => {
    const request = route.request();
    const url = new URL(request.url());
    throw new Error(`Unhandled API request in smoke test: ${request.method()} ${url.pathname}`);
  });
};

test.describe("frontend foundation smoke", () => {
  test("navigates to register and completes the registration flow", async ({ page }) => {
    await page.route("**/v1/**", async (route) => {
      const request = route.request();
      const method = request.method();
      const pathname = new URL(request.url()).pathname;

      if (method === "POST" && pathname === "/v1/users/register") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 11,
            username: "new_user",
            disabled: false,
            permissions: [],
          }),
        });
        return;
      }

      throw new Error(`Unhandled API request in register smoke: ${method} ${pathname}`);
    });

    await page.goto("/login");
    await page.getByRole("link", { name: t("auth.login.footer.createAccount") }).click();

    await expect(page).toHaveURL(/\/register$/);
    await page.getByLabel(t("auth.login.fields.username")).fill(" New_User ");
    await page.getByLabel(t("auth.login.fields.password")).fill("StrongPass1");
    await page.getByRole("button", { name: t("auth.register.submit.default") }).click();

    await expect(page.getByRole("heading", { name: t("auth.register.success.title") })).toBeVisible();
    await expect(page.getByText(t("auth.register.success.body", { username: "new_user" }))).toBeVisible();
  });

  test("completes login flow and lands on welcome page", async ({ page }) => {
    await page.route("**/v1/**", async (route) => {
      const request = route.request();
      const method = request.method();
      const pathname = new URL(request.url()).pathname;

      if (method === "POST" && pathname === "/v1/token") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            access_token: "smoke-access-token",
            token_type: "bearer",
          }),
        });
        return;
      }

      if (method === "GET" && pathname === "/v1/users/me") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            username: SMOKE_USERNAME,
            disabled: false,
            permissions: [
              "role_permissions:manage",
              "roles:manage",
              "user_roles:manage",
              "users:manage",
            ],
          }),
        });
        return;
      }

      throw new Error(`Unhandled API request in login smoke: ${method} ${pathname}`);
    });

    await page.goto("/login");

    await page.getByLabel(t("auth.login.fields.username")).fill(SMOKE_USERNAME);
    await page.getByLabel(t("auth.login.fields.password")).fill("smoke-password");
    await page.getByRole("button", { name: t("auth.login.submit.default") }).click();

    await expect(page).toHaveURL(/\/welcome$/);
    await expect(page.getByRole("heading", { name: t("welcome.greeting", { username: SMOKE_USERNAME }) })).toBeVisible();
  });

  test("redirects protected navigation to login when no session token exists", async ({ page }) => {
    await mockUnhandledApiRequests(page);

    await page.goto("/welcome");

    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("heading", { name: t("auth.login.title") })).toBeVisible();
  });

  test("renders protected-route error fallback with request-id diagnostics", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.sessionStorage.setItem(storageKey, "seed-token");
    }, ACCESS_TOKEN_STORAGE_KEY);

    await page.route("**/v1/**", async (route) => {
      const request = route.request();
      const method = request.method();
      const pathname = new URL(request.url()).pathname;

      if (method === "GET" && pathname === "/v1/users/me") {
        await route.fulfill({
          status: 500,
          headers: {
            "Content-Type": "application/json",
            "X-Request-ID": "req-e2e-500",
          },
          body: JSON.stringify({
            detail: "Unexpected backend error",
            code: "internal_error",
            request_id: "req-e2e-500",
          }),
        });
        return;
      }

      throw new Error(`Unhandled API request in protected-error smoke: ${method} ${pathname}`);
    });

    await page.goto("/welcome");

    await expect(page.getByRole("heading", { name: t("routing.protected.error.title") })).toBeVisible();
    await expect(page.getByText(/request_id=req-e2e-500/)).toBeVisible();
  });

  test("loads protected profile route and persists updated account state", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.sessionStorage.setItem(storageKey, "seed-token");
    }, ACCESS_TOKEN_STORAGE_KEY);

    await page.route("**/v1/**", async (route) => {
      const request = route.request();
      const method = request.method();
      const pathname = new URL(request.url()).pathname;

      if (method === "GET" && pathname === "/v1/users/me") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            username: SMOKE_USERNAME,
            disabled: false,
            permissions: [],
          }),
        });
        return;
      }

      if (method === "PATCH" && pathname === "/v1/users/me") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            username: "smoke-user-v2",
            disabled: false,
            permissions: [],
          }),
        });
        return;
      }

      throw new Error(`Unhandled API request in profile smoke: ${method} ${pathname}`);
    });

    await page.goto("/profile");

    await expect(page.getByRole("heading", { name: t("profile.title") })).toBeVisible();
    await page.getByLabel(t("profile.fields.username")).fill(" smoke-user-v2 ");
    await page.getByRole("button", { name: t("profile.submit.default") }).click();

    await expect(page.getByText(t("profile.success.body", { username: "smoke-user-v2" }))).toBeVisible();
    await expect(page.getByText(t("profile.currentUser", { username: "smoke-user-v2" }))).toBeVisible();
  });

  test("renders admin-users error diagnostics on forbidden RBAC access", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.sessionStorage.setItem(storageKey, "seed-token");
    }, ACCESS_TOKEN_STORAGE_KEY);

    await page.route("**/v1/**", async (route) => {
      const request = route.request();
      const method = request.method();
      const pathname = new URL(request.url()).pathname;

      if (method === "GET" && pathname === "/v1/users/me") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            username: SMOKE_USERNAME,
            disabled: false,
            permissions: ["users:manage"],
          }),
        });
        return;
      }

      if (method === "GET" && pathname === "/v1/rbac/users") {
        await route.fulfill({
          status: 403,
          headers: {
            "Content-Type": "application/json",
            "X-Request-ID": "req-admin-403",
          },
          body: JSON.stringify({
            detail: "Missing users:manage",
            code: "forbidden",
            request_id: "req-admin-403",
          }),
        });
        return;
      }

      if (method === "GET" && pathname === "/v1/rbac/roles") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([]),
        });
        return;
      }

      throw new Error(`Unhandled API request in admin-users forbidden smoke: ${method} ${pathname}`);
    });

    await page.goto("/admin/users");

    await expect(page.getByRole("heading", { name: t("admin.common.error.title") })).toBeVisible();
    await expect(page.getByText(/request_id=req-admin-403/)).toBeVisible();
  });

  test("redirects unauthorized direct admin routes to /welcome", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.sessionStorage.setItem(storageKey, "seed-token");
    }, ACCESS_TOKEN_STORAGE_KEY);

    await page.route("**/v1/**", async (route) => {
      const request = route.request();
      const method = request.method();
      const pathname = new URL(request.url()).pathname;

      if (method === "GET" && pathname === "/v1/users/me") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            username: SMOKE_USERNAME,
            disabled: false,
            permissions: [],
          }),
        });
        return;
      }

      throw new Error(`Unhandled API request in permission-redirect smoke: ${method} ${pathname}`);
    });

    await page.goto("/admin/users");
    await expect(page).toHaveURL(/\/welcome$/);
    await expect(page.getByRole("heading", { name: t("welcome.greeting", { username: SMOKE_USERNAME }) })).toBeVisible();

    await page.goto("/admin/roles");
    await expect(page).toHaveURL(/\/welcome$/);
    await expect(page.getByRole("heading", { name: t("welcome.greeting", { username: SMOKE_USERNAME }) })).toBeVisible();
  });
});
