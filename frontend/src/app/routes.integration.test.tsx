import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
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

    expect(await screen.findByRole("heading", { name: t("auth.login.title") })).toBeInTheDocument();
    expect(getAccessToken()).toBeNull();
  });
});
