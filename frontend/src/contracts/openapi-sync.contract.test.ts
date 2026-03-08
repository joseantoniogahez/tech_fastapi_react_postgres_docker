/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";

const OPENAPI_ARTIFACT_PATH = path.join(FRONTEND_DIR, "contracts", "openapi", "backend_openapi.json");

describe("openapi sync contracts", () => {
  it("keeps generated backend OpenAPI artifact available and parseable", () => {
    expect(fs.existsSync(OPENAPI_ARTIFACT_PATH)).toBe(true);

    const openapiText = fs.readFileSync(OPENAPI_ARTIFACT_PATH, "utf8");
    const openapi = JSON.parse(openapiText) as {
      openapi?: string;
      paths?: Record<string, Record<string, unknown>>;
    };

    expect(typeof openapi.openapi).toBe("string");
    expect(openapi.paths).toBeTruthy();
  });

  it("contains auth/session endpoints consumed by frontend", () => {
    const openapi = JSON.parse(fs.readFileSync(OPENAPI_ARTIFACT_PATH, "utf8")) as {
      paths: Record<string, Record<string, unknown>>;
    };

    const pathEntries = Object.entries(openapi.paths);
    const tokenEndpoint = pathEntries.find(([routePath]) => routePath.endsWith("/token"));
    const meEndpoint = pathEntries.find(([routePath]) => routePath.endsWith("/users/me"));

    expect(tokenEndpoint).toBeTruthy();
    expect(meEndpoint).toBeTruthy();
  });
});
