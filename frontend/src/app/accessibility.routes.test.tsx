import { QueryClientProvider } from "@tanstack/react-query";
import axe from "axe-core";
import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { createQueryClient } from "@/app/query-client";
import { appRoutes } from "@/app/routes";
import { clearAccessToken, setAccessToken } from "@/shared/auth/storage";
import { t } from "@/shared/i18n/ui-text";

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

    expect(await screen.findByRole("heading", { name: t("landing.title") })).toBeInTheDocument();
    expect((await axe.run(view.container, AXE_RUN_OPTIONS)).violations).toHaveLength(0);
  });

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
});
