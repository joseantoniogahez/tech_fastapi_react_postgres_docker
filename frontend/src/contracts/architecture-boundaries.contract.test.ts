/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";

const SOURCE_DIR = path.join(FRONTEND_DIR, "src");
const IMPORT_PATTERN = /^import\s+.*?\s+from\s+["'](?<specifier>[^"']+)["'];?$/gm;

const ROUTE_FILE_PATH = path.join(SOURCE_DIR, "app", "routes.tsx");
const PROTECTED_ROUTE_FILE_PATH = path.join(SOURCE_DIR, "shared", "routing", "ProtectedRoute.tsx");
const ROUTE_ERROR_BOUNDARY_FILE_PATH = path.join(SOURCE_DIR, "shared", "routing", "RouteErrorBoundary.tsx");

const toPosix = (value: string): string => value.replace(/\\/g, "/");

const collectRuntimeSourceFiles = (rootPath: string): string[] => {
  const entries = fs.readdirSync(rootPath, { withFileTypes: true });

  return entries.flatMap((entry) => {
    const absolutePath = path.join(rootPath, entry.name);
    if (entry.isDirectory()) {
      return collectRuntimeSourceFiles(absolutePath);
    }

    if (!absolutePath.endsWith(".ts") && !absolutePath.endsWith(".tsx")) {
      return [];
    }

    if (absolutePath.endsWith(".test.ts") || absolutePath.endsWith(".test.tsx")) {
      return [];
    }

    return [absolutePath];
  });
};

const extractImportSpecifiers = (sourceText: string): string[] => {
  const imports: string[] = [];
  let match = IMPORT_PATTERN.exec(sourceText);

  while (match !== null) {
    const specifier = match.groups?.specifier;
    if (specifier) {
      imports.push(specifier);
    }
    match = IMPORT_PATTERN.exec(sourceText);
  }

  IMPORT_PATTERN.lastIndex = 0;
  return imports;
};

describe("architecture boundary contracts", () => {
  it("prevents shared runtime modules from importing feature modules", () => {
    const violations: string[] = [];

    for (const filePath of collectRuntimeSourceFiles(path.join(SOURCE_DIR, "shared"))) {
      const sourceText = fs.readFileSync(filePath, "utf8");
      const imports = extractImportSpecifiers(sourceText);
      for (const specifier of imports) {
        if (!specifier.startsWith("@/features/")) {
          continue;
        }

        violations.push(`${toPosix(path.relative(FRONTEND_DIR, filePath))} -> ${specifier}`);
      }
    }

    expect(violations).toEqual([]);
  });

  it("prevents cross-feature runtime imports", () => {
    const violations: string[] = [];
    const featureRoot = path.join(SOURCE_DIR, "features");

    for (const filePath of collectRuntimeSourceFiles(featureRoot)) {
      const sourceText = fs.readFileSync(filePath, "utf8");
      const imports = extractImportSpecifiers(sourceText);
      const normalizedFilePath = toPosix(path.relative(featureRoot, filePath));
      const [featureName] = normalizedFilePath.split("/");

      for (const specifier of imports) {
        if (!specifier.startsWith("@/features/")) {
          continue;
        }

        const importedFeatureName = specifier.replace("@/features/", "").split("/")[0];
        if (importedFeatureName === featureName) {
          continue;
        }

        violations.push(`${toPosix(path.relative(FRONTEND_DIR, filePath))} -> ${specifier}`);
      }
    }

    expect(violations).toEqual([]);
  });

  it("keeps direct feature-page imports centralized in app/routes.tsx", () => {
    const violations: string[] = [];
    const appRoot = path.join(SOURCE_DIR, "app");

    for (const filePath of collectRuntimeSourceFiles(appRoot)) {
      if (path.resolve(filePath) === path.resolve(ROUTE_FILE_PATH)) {
        continue;
      }

      const sourceText = fs.readFileSync(filePath, "utf8");
      const imports = extractImportSpecifiers(sourceText);

      for (const specifier of imports) {
        if (!specifier.startsWith("@/features/")) {
          continue;
        }

        violations.push(`${toPosix(path.relative(FRONTEND_DIR, filePath))} -> ${specifier}`);
      }
    }

    expect(violations).toEqual([]);
  });

  it("enforces naming guardrails for route exports", () => {
    const routeSource = fs.readFileSync(ROUTE_FILE_PATH, "utf8");
    const protectedRouteSource = fs.readFileSync(PROTECTED_ROUTE_FILE_PATH, "utf8");
    const routeBoundarySource = fs.readFileSync(ROUTE_ERROR_BOUNDARY_FILE_PATH, "utf8");

    expect(routeSource).toMatch(/export const appRoutes\s*:/);
    expect(protectedRouteSource).toMatch(/export const ProtectedRoute\s*=/);
    expect(routeBoundarySource).toMatch(/export const RouteErrorBoundary\s*=/);
  });
});
