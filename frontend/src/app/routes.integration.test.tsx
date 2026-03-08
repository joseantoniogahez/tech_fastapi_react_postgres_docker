import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { appRoutes } from "@/app/routes";
import { createQueryClient } from "@/app/query-client";
import { t } from "@/shared/i18n/ui-text";
import { setAccessToken, getAccessToken } from "@/shared/auth/storage";

describe("routing integration", () => {
  it("clears expired token and redirects to login from protected route", async () => {
    setAccessToken("expired-token");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () =>
        Promise.resolve({
        detail: "Could not validate credentials",
        code: "unauthorized",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const queryClient = createQueryClient();
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/welcome"],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    );

    await waitFor(
      () => {
        expect(router.state.location.pathname).toBe("/login");
      },
      { timeout: 3_000 },
    );
    expect(await screen.findByRole("button", { name: t("auth.login.submit.default") })).toBeInTheDocument();
    expect(getAccessToken()).toBeNull();
  });

  it("shows protected-route diagnostic when session check fails with request id", async () => {
    setAccessToken("server-error-token");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      headers: {
        get: (header: string) => (header === "X-Request-ID" ? "req-protected-500" : null),
      },
      json: () =>
        Promise.resolve({
          detail: "Unexpected backend error",
          code: "internal_error",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);

    const queryClient = createQueryClient();
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/welcome"],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: t("routing.protected.error.title") })).toBeInTheDocument();
    expect(await screen.findByText(/request_id=req-protected-500/)).toBeInTheDocument();
  });

  it("renders explicit not-found page for unknown routes", async () => {
    const queryClient = createQueryClient();
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/unknown-route"],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: t("routing.notFound.title") })).toBeInTheDocument();
    expect(screen.getByText(t("routing.notFound.body"))).toBeInTheDocument();
  });
});
