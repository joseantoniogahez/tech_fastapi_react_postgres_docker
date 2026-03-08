import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { createQueryClient } from "@/app/query-client";
import { ApiError } from "@/shared/api/errors";
import { t } from "@/shared/i18n/ui-text";
import { RouteErrorBoundary } from "@/shared/routing/RouteErrorBoundary";

const renderBoundaryScenario = (buildError: () => unknown) => {
  const queryClient = createQueryClient();
  const router = createMemoryRouter(
    [
      {
        path: "/",
        loader: () => {
          throw buildError();
        },
        element: <h1>Home</h1>,
        errorElement: <RouteErrorBoundary />,
      },
    ],
    {
      initialEntries: ["/"],
    },
  );

  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
};

describe("RouteErrorBoundary", () => {
  it("renders route error fallback", async () => {
    renderBoundaryScenario(() => new Error("boom"));

    expect(await screen.findByRole("heading", { name: t("routing.error.title") })).toBeInTheDocument();
    expect(screen.getByText(t("routing.error.body"))).toBeInTheDocument();
  });

  it("renders request-id diagnostic for ApiError route failures", async () => {
    renderBoundaryScenario(() => new ApiError("failed", 500, "internal_error", "req-route-500"));

    expect(await screen.findByRole("heading", { name: t("routing.error.title") })).toBeInTheDocument();
    expect(screen.getByText(/request_id=req-route-500/)).toBeInTheDocument();
  });

  it("includes status details for route error responses", async () => {
    renderBoundaryScenario(
      () =>
        new Response("Not Found", {
          status: 404,
          statusText: "Not Found",
        }),
    );

    expect(await screen.findByRole("heading", { name: t("routing.error.title") })).toBeInTheDocument();
    expect(screen.getByText(`${t("routing.error.body")} (status=404)`)).toBeInTheDocument();
  });
});
