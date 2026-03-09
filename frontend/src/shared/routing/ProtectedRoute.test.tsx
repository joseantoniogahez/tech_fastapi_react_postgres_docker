import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { createQueryClient } from "@/app/query-client";
import { SESSION_QUERY_KEY, type AuthenticatedUser } from "@/shared/auth/session";
import { ProtectedRoute } from "@/shared/routing/ProtectedRoute";

const renderRoute = (sessionValue: AuthenticatedUser | null) => {
  const queryClient = createQueryClient();
  queryClient.setQueryData(SESSION_QUERY_KEY, sessionValue);

  const router = createMemoryRouter(
    [
      {
        path: "/login",
        element: <h1>Pantalla de login</h1>,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "/welcome",
            element: <h1>Pantalla privada</h1>,
          },
        ],
      },
    ],
    {
      initialEntries: ["/welcome"],
    }
  );

  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
};

describe("ProtectedRoute", () => {
  it("redirects to /login when there is no session user", async () => {
    renderRoute(null);

    expect(await screen.findByRole("heading", { name: "Pantalla de login" })).toBeInTheDocument();
  });

  it("renders private route when session user exists", async () => {
    renderRoute({
      id: 1,
      username: "admin",
      disabled: false,
      permissions: [],
    });

    expect(await screen.findByRole("heading", { name: "Pantalla privada" })).toBeInTheDocument();
  });
});
