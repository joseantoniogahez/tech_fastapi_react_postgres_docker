# Frontend Route Inventory

This document is the canonical inventory of runtime routes, access policies, and route-level ownership.

## Route Catalog

| Path       | Access Policy | Owner Module                      | Notes                                         |
| ---------- | ------------- | --------------------------------- | --------------------------------------------- |
| `/`        | `public`      | `features/landing/LandingPage`    | Root index route.                             |
| `/login`   | `public`      | `features/auth/LoginPage`         | User authentication page.                     |
| `/welcome` | `protected`   | `features/welcome/WelcomePage`    | Protected by `shared/routing/ProtectedRoute`. |
| `/*`       | `public`      | `features/not-found/NotFoundPage` | Explicit catch-all for unknown routes.        |

## Route-Level Error Handling

- Root route uses `shared/routing/RouteErrorBoundary` as `errorElement`.
- Route errors must render user-safe messages and include request-id diagnostics when available.

## 404 Behavior

- Unknown paths must resolve to `/*` and render `features/not-found/NotFoundPage`.
- Redirect-based 404 behavior is disallowed; the route tree must keep explicit not-found ownership.
