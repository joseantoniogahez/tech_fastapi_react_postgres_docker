/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import type { RouteObject } from "react-router-dom";

import { appRoutes } from "@/app/routes";
import { FRONTEND_DIR } from "@/contracts/docs";
import { ProtectedRoute } from "@/shared/routing/ProtectedRoute";
import { RouteErrorBoundary } from "@/shared/routing/RouteErrorBoundary";

const ROUTE_INVENTORY_PATH = path.join(FRONTEND_DIR, "docs", "operations", "route_inventory.md");
const ROUTE_ROW_PATTERN = /^\|\s*`(?<path>\/[^`]*)`\s*\|\s*`(?<access>public|protected)`\s*\|\s*`(?<owner>[^`]+)`\s*\|/gm;

const ROUTE_OWNER_BY_COMPONENT: Record<string, string> = {
  AdminAssignmentsPage: "features/admin-assignments/AdminAssignmentsPage",
  AdminPermissionsPage: "features/admin-permissions/AdminPermissionsPage",
  AdminRolesPage: "features/admin-roles/AdminRolesPage",
  AdminUsersPage: "features/admin-users/AdminUsersPage",
  LandingPage: "features/landing/LandingPage",
  LoginPage: "features/auth/LoginPage",
  NotFoundPage: "features/not-found/NotFoundPage",
  ProfilePage: "features/profile/ProfilePage",
  RegisterPage: "features/auth/RegisterPage",
  WelcomePage: "features/welcome/WelcomePage",
};

interface RouteContractRow {
  path: string;
  access: "public" | "protected";
  owner: string;
}

const getElementTypeName = (element: unknown): string | null => {
  if (typeof element !== "object" || element === null || !("type" in element)) {
    return null;
  }

  const routeElementType = (element as { type: unknown }).type;
  return typeof routeElementType === "function" ? routeElementType.name : null;
};

const normalizePath = (parentPath: string, routePath: string): string => {
  if (routePath === "*") {
    return parentPath === "/" ? "/*" : `${parentPath.replace(/\/+$/, "")}/*`;
  }

  if (routePath.startsWith("/")) {
    return routePath;
  }

  const sanitizedParent = parentPath.endsWith("/") ? parentPath.slice(0, -1) : parentPath;
  return `${sanitizedParent}/${routePath}`;
};

const collectRouteRows = (
  routes: RouteObject[],
  context: { path: string; access: "public" | "protected" },
): RouteContractRow[] => {
  const rows: RouteContractRow[] = [];

  for (const route of routes) {
    const routeElementName = getElementTypeName(route.element);
    const routeOwner = routeElementName ? ROUTE_OWNER_BY_COMPONENT[routeElementName] : undefined;
    const access = routeElementName === ProtectedRoute.name ? "protected" : context.access;

    const routePath =
      route.index === true
        ? context.path
        : typeof route.path === "string"
          ? normalizePath(context.path, route.path)
          : context.path;

    if (routeOwner) {
      rows.push({
        path: routePath,
        access,
        owner: routeOwner,
      });
    }

    if (route.children) {
      rows.push(...collectRouteRows(route.children, { path: routePath, access }));
    }
  }

  return rows;
};

const parseDocumentedRows = (markdown: string): RouteContractRow[] => {
  const rows: RouteContractRow[] = [];
  let match = ROUTE_ROW_PATTERN.exec(markdown);

  while (match !== null) {
    const routePath = match.groups?.path;
    const access = match.groups?.access;
    const owner = match.groups?.owner;
    if (routePath && access && owner) {
      rows.push({
        path: routePath,
        access: access as "public" | "protected",
        owner,
      });
    }
    match = ROUTE_ROW_PATTERN.exec(markdown);
  }
  ROUTE_ROW_PATTERN.lastIndex = 0;

  return rows;
};

describe("route inventory contracts", () => {
  it("keeps route inventory docs aligned with the router configuration", () => {
    const markdown = fs.readFileSync(ROUTE_INVENTORY_PATH, "utf8");
    const documentedRows = parseDocumentedRows(markdown)
      .map((row) => `${row.path}|${row.access}|${row.owner}`)
      .sort();

    const actualRows = collectRouteRows(appRoutes, { path: "/", access: "public" })
      .map((row) => `${row.path}|${row.access}|${row.owner}`)
      .sort();

    expect(documentedRows).toEqual(actualRows);
  });

  it("documents explicit 404 and route error behavior", () => {
    const markdown = fs.readFileSync(ROUTE_INVENTORY_PATH, "utf8");

    expect(markdown).toContain("## Route-Level Error Handling");
    expect(markdown).toContain("## 404 Behavior");
    expect(markdown).toContain("`/*`");
    expect(markdown).toContain("`/register`");
    expect(markdown).toContain("`/profile`");
    expect(markdown).toContain("Requires `user_roles:manage`; missing permission redirects to `/welcome`.");
    expect(markdown).toContain("Requires `role_permissions:manage`; role inventory falls back to manual ID without `roles:manage`.");
    expect(markdown).toContain(
      "Requires `users:manage`; missing permission redirects to `/welcome`, while role-related controls stay hidden in-page unless the session also has `roles:manage`.",
    );
    expect(markdown).toContain("Requires `roles:manage`; missing permission redirects to `/welcome`.");
  });

  it("keeps root route error boundary ownership explicit in route tree", () => {
    const [rootRoute] = appRoutes;
    const errorElement = rootRoute.errorElement;

    expect(errorElement).toBeTruthy();
    expect(getElementTypeName(errorElement)).toBe(RouteErrorBoundary.name);
  });
});
