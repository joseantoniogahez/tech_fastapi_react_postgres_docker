import { QueryClientProvider } from "@tanstack/react-query";
import axe from "axe-core";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { createQueryClient } from "@/app/query-client";
import { appRoutes } from "@/app/routes";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { SESSION_QUERY_KEY } from "@/shared/auth/session";
import { clearAccessToken } from "@/shared/auth/storage";
import { t } from "@/shared/i18n/ui-text";

const AXE_RUN_OPTIONS: axe.RunOptions = {
  rules: {
    "color-contrast": { enabled: false },
  },
};

const renderRegisterPage = () => {
  const queryClient = createQueryClient();
  queryClient.setQueryData(SESSION_QUERY_KEY, null);

  const router = createMemoryRouter(
    [
      {
        path: "/register",
        element: <RegisterPage />,
      },
      {
        path: "/login",
        element: <h1>{t("auth.login.title")}</h1>,
      },
      {
        path: "/welcome",
        element: <h1>{t("welcome.badge")}</h1>,
      },
    ],
    {
      initialEntries: ["/register"],
    },
  );

  const view = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );

  return { queryClient, router, view };
};

describe("RegisterPage", () => {
  beforeEach(() => {
    clearAccessToken();
  });

  it("renders on the public /register route", async () => {
    const queryClient = createQueryClient();
    queryClient.setQueryData(SESSION_QUERY_KEY, null);
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/register"],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    );

    expect(await screen.findByRole("heading", { name: t("auth.register.title") })).toBeInTheDocument();
  });

  it("creates a new account and shows success state without mutating session", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: () =>
        Promise.resolve({
          id: 9,
          username: "new_user",
          disabled: false,
          permissions: [],
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    const { queryClient } = renderRegisterPage();

    await user.type(screen.getByLabelText(t("auth.login.fields.username")), " New_User ");
    await user.type(screen.getByLabelText(t("auth.login.fields.password")), "StrongPass1");
    await user.click(screen.getByRole("button", { name: t("auth.register.submit.default") }));

    expect(await screen.findByRole("heading", { name: t("auth.register.success.title") })).toBeInTheDocument();
    expect(screen.getByText(t("auth.register.success.body", { username: "new_user" }))).toBeInTheDocument();
    expect(queryClient.getQueryData(SESSION_QUERY_KEY)).toBeNull();
  });

  it("shows backend failure diagnostics on registration error", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      headers: {
        get: (header: string) => (header === "X-Request-ID" ? "req-register-400" : null),
      },
      json: () =>
        Promise.resolve({
          detail: "Password does not meet policy",
          code: "invalid_input",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderRegisterPage();

    await user.type(screen.getByLabelText(t("auth.login.fields.username")), "new_user");
    await user.type(screen.getByLabelText(t("auth.login.fields.password")), "ValidPass1");
    await user.click(screen.getByRole("button", { name: t("auth.register.submit.default") }));

    expect(
      await screen.findByText("Password does not meet policy (request_id=req-register-400)"),
    ).toBeInTheDocument();
  });

  it("keeps the registration form accessible", async () => {
    const { view } = renderRegisterPage();

    expect(await screen.findByRole("heading", { name: t("auth.register.title") })).toBeInTheDocument();
    expect((await axe.run(view.container, AXE_RUN_OPTIONS)).violations).toHaveLength(0);
  });

  it("redirects authenticated users away from /register", async () => {
    const queryClient = createQueryClient();
    queryClient.setQueryData(SESSION_QUERY_KEY, {
      id: 1,
      username: "admin",
      disabled: false,
      permissions: [],
    });
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/register"],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe("/welcome");
    });
  });
});
