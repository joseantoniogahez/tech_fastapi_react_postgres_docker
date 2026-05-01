/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";
import {
  RBAC_PERMISSIONS_ENDPOINT_PATH,
  RBAC_ROLE_USERS_ENDPOINT_PATH_TEMPLATE,
  RBAC_ROLES_ENDPOINT_PATH,
  RBAC_USER_ROLE_ENDPOINT_PATH_TEMPLATE,
  RBAC_USER_ROLES_ENDPOINT_PATH_TEMPLATE,
  RBAC_USERS_ENDPOINT_PATH,
} from "@/shared/rbac/admin";
import { CURRENT_USER_ENDPOINT_PATH, REGISTER_USER_ENDPOINT_PATH, TOKEN_ENDPOINT_PATH } from "@/shared/auth/session";

const MATRIX_PATH = path.join(FRONTEND_DIR, "docs", "operations", "api_consumer_matrix.md");
const CATALOG_ROW_PATTERN =
  /^\|\s*`(?<endpoint>\/[^`]*)`\s*\|\s*`(?<method>[A-Z]+)`\s*\|\s*`(?<module>[^`]+)`\s*\|\s*`(?<consumer>[^`]+)`\s*\|\s*`(?<auth>[^`]+)`\s*\|/gm;

interface CatalogRow {
  endpoint: string;
  method: string;
  module: string;
  consumer: string;
  auth: string;
}

const parseCatalogRows = (markdown: string): CatalogRow[] => {
  const rows: CatalogRow[] = [];
  let match = CATALOG_ROW_PATTERN.exec(markdown);

  while (match !== null) {
    const endpoint = match.groups?.endpoint;
    const method = match.groups?.method;
    const module = match.groups?.module;
    const consumer = match.groups?.consumer;
    const auth = match.groups?.auth;

    if (endpoint && method && module && consumer && auth) {
      rows.push({
        endpoint,
        method,
        module,
        consumer,
        auth,
      });
    }

    match = CATALOG_ROW_PATTERN.exec(markdown);
  }
  CATALOG_ROW_PATTERN.lastIndex = 0;

  return rows;
};

describe("api consumer matrix contracts", () => {
  it("keeps consumer catalog aligned with auth/session API consumers", () => {
    const markdown = fs.readFileSync(MATRIX_PATH, "utf8");
    const rows = parseCatalogRows(markdown);

    const endpointKeys = rows.map((row) => `${row.endpoint}|${row.method}|${row.consumer}`).sort();

    expect(endpointKeys).toContain(`${TOKEN_ENDPOINT_PATH}|POST|loginWithCredentials`);
    expect(endpointKeys).toContain(`${REGISTER_USER_ENDPOINT_PATH}|POST|registerUser`);
    expect(endpointKeys).toContain(`${CURRENT_USER_ENDPOINT_PATH}|GET|readCurrentUser`);
    expect(endpointKeys).toContain(`${CURRENT_USER_ENDPOINT_PATH}|PATCH|updateCurrentUser`);
    expect(endpointKeys).toContain(`${RBAC_USERS_ENDPOINT_PATH}|GET|readAdminUsers`);
    expect(endpointKeys).toContain(`${RBAC_USERS_ENDPOINT_PATH}|POST|createAdminUser`);
    expect(endpointKeys).toContain(`${RBAC_USER_ROLES_ENDPOINT_PATH_TEMPLATE}|GET|readRbacUserRoles`);
    expect(endpointKeys).toContain(`${RBAC_USER_ROLE_ENDPOINT_PATH_TEMPLATE}|PUT|assignRbacUserRole`);
    expect(endpointKeys).toContain(`${RBAC_USER_ROLE_ENDPOINT_PATH_TEMPLATE}|DELETE|removeRbacUserRole`);
    expect(endpointKeys).toContain(`${RBAC_ROLES_ENDPOINT_PATH}|GET|readRbacRoles`);
    expect(endpointKeys).toContain(`${RBAC_ROLES_ENDPOINT_PATH}|POST|createRbacRole`);
    expect(endpointKeys).toContain(`${RBAC_ROLE_USERS_ENDPOINT_PATH_TEMPLATE}|GET|readRbacRoleUsers`);
    expect(endpointKeys).toContain(`${RBAC_PERMISSIONS_ENDPOINT_PATH}|GET|readRbacPermissions`);
    expect(endpointKeys).toContain(`/rbac/roles/{role_id}/permissions/{permission_id}|PUT|assignRbacRolePermission`);
    expect(endpointKeys).toContain(`/rbac/roles/{role_id}/permissions/{permission_id}|DELETE|removeRbacRolePermission`);
  });

  it("documents request-id and normalized error behavior for auth/session endpoints", () => {
    const markdown = fs.readFileSync(MATRIX_PATH, "utf8");

    expect(markdown).toContain("| `/token`");
    expect(markdown).toContain("| `/users/register`");
    expect(markdown).toContain("| `/users/me`");
    expect(markdown).toContain("X-Request-ID");
    expect(markdown).toContain("request_id");
    expect(markdown).toContain("permissions[]");
    expect(markdown).toContain("unauthorized");
    expect(markdown).toContain("forbidden");
    expect(markdown).toContain("conflict");
    expect(markdown).toContain("internal_error");
    expect(markdown).toContain("network_error");
    expect(markdown).toContain(
      "`readRbacRoles` is permission-gated on `/admin/users`: the page only requests `/rbac/roles` when the current session has `roles:manage`; otherwise it hides role-related controls and does not send `role_ids`.",
    );
  });
});
