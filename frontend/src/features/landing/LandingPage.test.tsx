import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { createQueryClient } from "@/app/query-client";
import { SESSION_QUERY_KEY } from "@/shared/auth/session";
import { t } from "@/shared/i18n/ui-text";
import { LandingPage } from "@/features/landing/LandingPage";

describe("LandingPage", () => {
  it("renders CTA to login", () => {
    const queryClient = createQueryClient();
    queryClient.setQueryData(SESSION_QUERY_KEY, null);
    const router = createMemoryRouter(
      [
        {
          path: "/",
          element: <LandingPage />,
        },
      ],
      { initialEntries: ["/"] }
    );

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    );

    expect(screen.getByRole("heading", { name: t("landing.title") })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: t("landing.cta.login") })).toHaveAttribute("href", "/login");
  });
});
