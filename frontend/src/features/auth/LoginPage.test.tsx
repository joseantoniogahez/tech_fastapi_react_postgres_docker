import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { createQueryClient } from "@/app/query-client";
import { SESSION_QUERY_KEY } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { LoginPage } from "@/features/auth/LoginPage";

const renderLogin = () => {
  const queryClient = createQueryClient();
  queryClient.setQueryData(SESSION_QUERY_KEY, null);
  const router = createMemoryRouter(
    [
      {
        path: "/login",
        element: <LoginPage />,
      },
      {
        path: "/welcome",
        element: <h1>Pantalla de bienvenida</h1>,
      },
    ],
    {
      initialEntries: ["/login"],
    }
  );

  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
};

describe("LoginPage", () => {
  it("completes login flow and redirects to welcome", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
          access_token: "valid-token",
          token_type: "bearer",
          }),
      } satisfies Partial<Response>)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
          id: 1,
          username: "admin",
          disabled: false,
          }),
      } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderLogin();

    await user.type(screen.getByLabelText(t("auth.login.fields.username")), "admin");
    await user.type(screen.getByLabelText(t("auth.login.fields.password")), "admin123");
    await user.click(screen.getByRole("button", { name: t("auth.login.submit.default") }));

    expect(await screen.findByRole("heading", { name: "Pantalla de bienvenida" })).toBeInTheDocument();
  });

  it("shows backend error message on invalid credentials", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: () =>
        Promise.resolve({
        detail: "Invalid username or password",
        code: "unauthorized",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderLogin();

    await user.type(screen.getByLabelText(t("auth.login.fields.username")), "admin");
    await user.type(screen.getByLabelText(t("auth.login.fields.password")), "wrong");
    await user.click(screen.getByRole("button", { name: t("auth.login.submit.default") }));

    expect(await screen.findByText("Invalid username or password")).toBeInTheDocument();
  });

  it("shows request-id diagnostic when backend returns correlation header", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      headers: {
        get: (header: string) => (header === "X-Request-ID" ? "req-login-500" : null),
      },
      json: () =>
        Promise.resolve({
          detail: "Unexpected error",
          code: "internal_error",
        }),
    } satisfies Partial<Response>);
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderLogin();

    await user.type(screen.getByLabelText(t("auth.login.fields.username")), "admin");
    await user.type(screen.getByLabelText(t("auth.login.fields.password")), "wrong");
    await user.click(screen.getByRole("button", { name: t("auth.login.submit.default") }));

    expect(await screen.findByText("Unexpected error (request_id=req-login-500)")).toBeInTheDocument();
  });
});
