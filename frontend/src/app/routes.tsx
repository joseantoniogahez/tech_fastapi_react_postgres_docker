import type { RouteObject } from "react-router-dom";

import { AdminRolesPage } from "@/features/admin-roles/AdminRolesPage";
import { AdminUsersPage } from "@/features/admin-users/AdminUsersPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { NotFoundPage } from "@/features/not-found/NotFoundPage";
import { WelcomePage } from "@/features/welcome/WelcomePage";
import { ProtectedRoute } from "@/shared/routing/ProtectedRoute";
import { PermissionRoute } from "@/shared/routing/PermissionRoute";
import { RootLayout } from "@/shared/routing/RootLayout";
import { RouteErrorBoundary } from "@/shared/routing/RouteErrorBoundary";
import { IAM_PERMISSION } from "@/shared/iam/contracts";

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
          {
            element: <PermissionRoute requiredPermission={IAM_PERMISSION.USERS_MANAGE} />,
            children: [
              {
                path: "admin/users",
                element: <AdminUsersPage />,
              },
            ],
          },
          {
            element: <PermissionRoute requiredPermission={IAM_PERMISSION.ROLES_MANAGE} />,
            children: [
              {
                path: "admin/roles",
                element: <AdminRolesPage />,
              },
            ],
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
