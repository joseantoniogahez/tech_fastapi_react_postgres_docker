import { QueryClientProvider } from "@tanstack/react-query";
import axe from "axe-core";
import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { createQueryClient } from "@/app/query-client";
import { appRoutes } from "@/app/routes";
import { clearAccessToken, setAccessToken } from "@/shared/auth/storage";
import { t } from "@/shared/i18n/ui-text";

const toRequestPathname = (input: RequestInfo | URL): string => {
  if (input instanceof URL) {
    return input.pathname;
  }
  if (typeof input === "string") {
    return new URL(input).pathname;
  }
  return new URL(input.url).pathname;
};

const AXE_RUN_OPTIONS: axe.RunOptions = {
  rules: {
    "color-contrast": { enabled: false },
  },
};

const renderRoute = (initialEntries: string[]) => {
  const queryClient = createQueryClient();
  const router = createMemoryRouter(appRoutes, { initialEntries });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
};

describe("accessibility route baseline", () => {
  it("has no obvious accessibility violations on landing route", async () => {
    clearAccessToken();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network unreachable")));

    const view = renderRoute(["/"]);

    expect(
      await screen.findByRole("heading", { name: t("landing.title") }, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect((await axe.run(view.container, AXE_RUN_OPTIONS)).violations).toHaveLength(0);
  }, 10_000);

  it("has no obvious accessibility violations on login route", async () => {
    const view = renderRoute(["/login"]);

    expect(await screen.findByRole("heading", { name: t("auth.login.title") })).toBeInTheDocument();
    expect((await axe.run(view.container, AXE_RUN_OPTIONS)).violations).toHaveLength(0);
  });

  it("has no obvious accessibility violations on protected error state", async () => {
    setAccessToken("token-with-server-error");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      headers: {
        get: (header: string) => (header === "X-Request-ID" ? "req-a11y-500" : null),
      },
      json: () =>
        Promise.resolve({
          detail: "Unexpected backend error",
          code: "internal_error",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const view = renderRoute(["/welcome"]);

    expect(await screen.findByRole("heading", { name: t("routing.protected.error.title") })).toBeInTheDocument();
    expect((await axe.run(view.container, AXE_RUN_OPTIONS)).violations).toHaveLength(0);
  });

  it("has no obvious accessibility violations on admin users route", async () => {
    setAccessToken("admin-token");

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const pathname = toRequestPathname(input);
      if (pathname === "/v1/users/me") {
        return {
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              id: 1,
              username: "admin",
              disabled: false,
              permissions: ["users:manage"],
            }),
        } satisfies Partial<Response>;
      }

      if (pathname === "/v1/rbac/users") {
        return {
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        } satisfies Partial<Response>;
      }

      if (pathname === "/v1/rbac/roles") {
        return {
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        } satisfies Partial<Response>;
      }

      throw new Error(`Unhandled accessibility request: ${pathname}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const view = renderRoute(["/admin/users"]);

    expect(await screen.findByRole("heading", { name: t("admin.users.title") })).toBeInTheDocument();
    expect((await axe.run(view.container, AXE_RUN_OPTIONS)).violations).toHaveLength(0);
  });

  it("has no obvious accessibility violations on admin assignments route", async () => {
    setAccessToken("assignment-admin-token");

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const pathname = toRequestPathname(input);
      if (pathname === "/v1/users/me") {
        return {
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              id: 1,
              username: "rbac_admin",
              disabled: false,
              permissions: ["user_roles:manage"],
            }),
        } satisfies Partial<Response>;
      }

      throw new Error(`Unhandled accessibility request: ${pathname}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const view = renderRoute(["/admin/assignments"]);

    expect(await screen.findByRole("heading", { name: t("admin.as.title") })).toBeInTheDocument();
    expect((await axe.run(view.container, AXE_RUN_OPTIONS)).violations).toHaveLength(0);
  });

  it("has no obvious accessibility violations on admin permissions route", async () => {
    setAccessToken("permission-admin-token");

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const pathname = toRequestPathname(input);
      if (pathname === "/v1/users/me") {
        return {
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              id: 1,
              username: "permission_admin",
              disabled: false,
              permissions: ["role_permissions:manage"],
            }),
        } satisfies Partial<Response>;
      }

      if (pathname === "/v1/rbac/permissions") {
        return {
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve([
              {
                id: "users:manage",
                name: "Manage users",
              },
            ]),
        } satisfies Partial<Response>;
      }

      throw new Error(`Unhandled accessibility request: ${pathname}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const view = renderRoute(["/admin/permissions"]);

    expect(await screen.findByRole("heading", { name: t("admin.pm.title") })).toBeInTheDocument();
    expect(await screen.findByLabelText(t("admin.roles.permissions.select"))).toBeInTheDocument();
    expect((await axe.run(view.container, AXE_RUN_OPTIONS)).violations).toHaveLength(0);
  });
});
