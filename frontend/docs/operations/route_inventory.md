# Frontend Route Inventory

This document is the canonical inventory of runtime routes, access policies, and route-level ownership.

## Route Catalog

| Path                 | Access Policy | Owner Module                                      | Notes                                                                                              |
| -------------------- | ------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `/`                  | `public`      | `features/landing/LandingPage`                    | Root index route.                                                                                  |
| `/login`             | `public`      | `features/auth/LoginPage`                         | User authentication page.                                                                          |
| `/register`          | `public`      | `features/auth/RegisterPage`                      | Public self-service registration; successful submit does not create a session token.               |
| `/welcome`           | `protected`   | `features/welcome/WelcomePage`                    | Protected by `shared/routing/ProtectedRoute`.                                                      |
| `/profile`           | `protected`   | `features/profile/ProfilePage`                    | Protected by `shared/routing/ProtectedRoute`; updates authenticated username/password.             |
| `/admin/assignments` | `protected`   | `features/admin-assignments/AdminAssignmentsPage` | Requires `user_roles:manage`; missing permission redirects to `/welcome`.                          |
| `/admin/permissions` | `protected`   | `features/admin-permissions/AdminPermissionsPage` | Requires `role_permissions:manage`; role inventory falls back to manual ID without `roles:manage`. |
| `/admin/users`       | `protected`   | `features/admin-users/AdminUsersPage`             | Requires `users:manage`; missing permission redirects to `/welcome`.                               |
| `/admin/roles`       | `protected`   | `features/admin-roles/AdminRolesPage`             | Requires `roles:manage`; missing permission redirects to `/welcome`.                               |
| `/*`                 | `public`      | `features/not-found/NotFoundPage`                 | Explicit catch-all for unknown routes.                                                             |

## Route-Level Error Handling

- Root route uses `shared/routing/RouteErrorBoundary` as `errorElement`.
- Protected route failures render user-safe messages and include request-id diagnostics when available.
- Route errors must render user-safe messages and include request-id diagnostics when available.

## 404 Behavior

- Unknown paths must resolve to `/*` and render `features/not-found/NotFoundPage`.
- Redirect-based 404 behavior is disallowed; the route tree must keep explicit not-found ownership.
