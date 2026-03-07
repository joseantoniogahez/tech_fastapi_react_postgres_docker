import { Navigate, type RouteObject } from "react-router-dom";

import { LoginPage } from "@/features/auth/LoginPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { WelcomePage } from "@/features/welcome/WelcomePage";
import { ProtectedRoute } from "@/shared/routing/ProtectedRoute";

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <LandingPage />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: "/welcome",
        element: <WelcomePage />,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
];
