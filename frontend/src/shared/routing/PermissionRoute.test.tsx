import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { appRoutes } from "@/app/routes";
import { createQueryClient } from "@/app/query-client";
import { SESSION_QUERY_KEY } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";

const renderAppAt = (path: "/admin/users" | "/admin/roles") => {
  const queryClient = createQueryClient();
  queryClient.setQueryData(SESSION_QUERY_KEY, {
    id: 7,
    username: "reader_user",
    disabled: false,
    permissions: [],
  });

  const router = createMemoryRouter(appRoutes, {
    initialEntries: [path],
  });

  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );

  return router;
};

describe("PermissionRoute", () => {
  it("redirects unauthorized direct navigation from /admin/users to /welcome", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const router = renderAppAt("/admin/users");

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/welcome");
    });
    expect(
      await screen.findByRole("heading", { name: t("welcome.greeting", { username: "reader_user" }) }),
    ).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  }, 10_000);

  it("redirects unauthorized direct navigation from /admin/roles to /welcome", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const router = renderAppAt("/admin/roles");

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/welcome");
    });
    expect(
      await screen.findByRole("heading", { name: t("welcome.greeting", { username: "reader_user" }) }),
    ).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  }, 10_000);
});
