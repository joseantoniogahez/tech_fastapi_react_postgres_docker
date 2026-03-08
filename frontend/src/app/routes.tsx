import type { RouteObject } from "react-router-dom";

import { LoginPage } from "@/features/auth/LoginPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { NotFoundPage } from "@/features/not-found/NotFoundPage";
import { WelcomePage } from "@/features/welcome/WelcomePage";
import { ProtectedRoute } from "@/shared/routing/ProtectedRoute";
import { RootLayout } from "@/shared/routing/RootLayout";
import { RouteErrorBoundary } from "@/shared/routing/RouteErrorBoundary";

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <RouteErrorBoundary />,
    children: [
      {
        index: true,
        element: <LandingPage />,
      },
      {
        path: "login",
        element: <LoginPage />,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "welcome",
            element: <WelcomePage />,
          },
        ],
      },
      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
];
