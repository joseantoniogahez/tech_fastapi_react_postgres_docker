import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { createQueryClient } from "@/app/query-client";
import { SESSION_QUERY_KEY, type AuthenticatedUser } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { IAM_PERMISSION } from "@/shared/iam/contracts";
import { RootLayout } from "@/shared/routing/RootLayout";

const renderLayout = (sessionValue: AuthenticatedUser | null) => {
  const queryClient = createQueryClient();
  queryClient.setQueryData(SESSION_QUERY_KEY, sessionValue);

  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <RootLayout />,
        children: [
          {
            path: "welcome",
            element: <h1>{t("welcome.badge")}</h1>,
          },
        ],
      },
    ],
    {
      initialEntries: ["/welcome"],
    },
  );

  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
};

describe("RootLayout", () => {
  it("does not render navigation menu trigger without authenticated session", async () => {
    renderLayout(null);

    expect(await screen.findByRole("heading", { name: t("welcome.badge") })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: t("routing.nav.menu.toggle") })).not.toBeInTheDocument();
  });

  it("renders hamburger menu for authenticated session and filters admin items by permissions", async () => {
    renderLayout({
      id: 1,
      username: "admin",
      disabled: false,
      permissions: [IAM_PERMISSION.USER_ROLES_MANAGE, IAM_PERMISSION.USERS_MANAGE],
    });

    const menuTrigger = await screen.findByRole("button", { name: t("routing.nav.menu.toggle") });
    expect(menuTrigger).toHaveAttribute("aria-expanded", "false");

    const user = userEvent.setup();
    await user.click(menuTrigger);

    expect(menuTrigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getAllByRole("link", { name: t("routing.nav.home") })).not.toHaveLength(0);
    expect(screen.getByRole("link", { name: t("routing.nav.profile") })).toBeInTheDocument();
    expect(screen.getByText(t("routing.nav.admin.group"))).toBeInTheDocument();
    expect(screen.getByRole("link", { name: t("routing.nav.admin.assignments") })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: t("routing.nav.admin.permissions") })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: t("routing.nav.admin.users") })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: t("routing.nav.admin.roles") })).not.toBeInTheDocument();
  });

  it("shows assignments nav item for user_roles:manage without users:manage", async () => {
    renderLayout({
      id: 4,
      username: "rbac_admin",
      disabled: false,
      permissions: [IAM_PERMISSION.USER_ROLES_MANAGE],
    });

    const menuTrigger = await screen.findByRole("button", { name: t("routing.nav.menu.toggle") });
    const user = userEvent.setup();
    await user.click(menuTrigger);

    expect(screen.getByRole("link", { name: t("routing.nav.admin.assignments") })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: t("routing.nav.admin.users") })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: t("routing.nav.admin.roles") })).not.toBeInTheDocument();
  });

  it("shows permissions nav item for role_permissions:manage without roles:manage", async () => {
    renderLayout({
      id: 5,
      username: "permission_admin",
      disabled: false,
      permissions: [IAM_PERMISSION.ROLE_PERMISSIONS_MANAGE],
    });

    const menuTrigger = await screen.findByRole("button", { name: t("routing.nav.menu.toggle") });
    const user = userEvent.setup();
    await user.click(menuTrigger);

    expect(screen.getByRole("link", { name: t("routing.nav.admin.permissions") })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: t("routing.nav.admin.roles") })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: t("routing.nav.admin.users") })).not.toBeInTheDocument();
  });
});
