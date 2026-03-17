import type { RouteObject } from "react-router-dom";

import { AdminAssignmentsPage } from "@/features/admin-assignments/AdminAssignmentsPage";
import { AdminPermissionsPage } from "@/features/admin-permissions/AdminPermissionsPage";
import { AdminRolesPage } from "@/features/admin-roles/AdminRolesPage";
import { AdminUsersPage } from "@/features/admin-users/AdminUsersPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { NotFoundPage } from "@/features/not-found/NotFoundPage";
import { ProfilePage } from "@/features/profile/ProfilePage";
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
        path: "register",
        element: <RegisterPage />,
      },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "welcome",
            element: <WelcomePage />,
          },
          {
            path: "profile",
            element: <ProfilePage />,
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
          {
            element: <PermissionRoute requiredPermission={IAM_PERMISSION.ROLE_PERMISSIONS_MANAGE} />,
            children: [
              {
                path: "admin/permissions",
                element: <AdminPermissionsPage />,
              },
            ],
          },
          {
            element: <PermissionRoute requiredPermission={IAM_PERMISSION.USER_ROLES_MANAGE} />,
            children: [
              {
                path: "admin/assignments",
                element: <AdminAssignmentsPage />,
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
