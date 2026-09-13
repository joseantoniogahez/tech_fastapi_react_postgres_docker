/// <reference types="node" />

import fs from "node:fs";
import path from "node:path";

import { FRONTEND_DIR } from "@/contracts/docs";

type Rgb = readonly [number, number, number];

const STYLES_PATH = path.join(FRONTEND_DIR, "src", "app", "styles.css");
const FIELD_SOURCE_PATHS = [
  path.join(FRONTEND_DIR, "src", "features", "auth", "LoginPage.tsx"),
  path.join(FRONTEND_DIR, "src", "features", "auth", "RegisterPage.tsx"),
  path.join(FRONTEND_DIR, "src", "features", "profile", "ProfilePage.tsx"),
  path.join(FRONTEND_DIR, "src", "shared", "rbac", "ui.tsx"),
] as const;
const TOKEN_PATTERN = /--(?<name>app-(?:bg|surface|subtle|border)):\s*(?<value>#[0-9a-f]{6});/gi;
const WASH_PATTERN = /rgba\((?<red>\d+),\s*(?<green>\d+),\s*(?<blue>\d+),\s*(?<alpha>0\.\d+)\)/g;

const toRgb = (hexColor: string): Rgb => [
  Number.parseInt(hexColor.slice(1, 3), 16),
  Number.parseInt(hexColor.slice(3, 5), 16),
  Number.parseInt(hexColor.slice(5, 7), 16),
];

const blend = (foreground: Rgb, background: Rgb, alpha: number): Rgb => [
  Math.round(foreground[0] * alpha + background[0] * (1 - alpha)),
  Math.round(foreground[1] * alpha + background[1] * (1 - alpha)),
  Math.round(foreground[2] * alpha + background[2] * (1 - alpha)),
];

const relativeLuminance = (color: Rgb): number => {
  const linearize = (channel: number): number => {
    const normalized = channel / 255;
    return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
  };
  const [red, green, blue] = [linearize(color[0]), linearize(color[1]), linearize(color[2])];
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
};

const contrastRatio = (first: Rgb, second: Rgb): number => {
  const firstLuminance = relativeLuminance(first);
  const secondLuminance = relativeLuminance(second);
  return (Math.max(firstLuminance, secondLuminance) + 0.05) / (Math.min(firstLuminance, secondLuminance) + 0.05);
};

const requireToken = (tokens: ReadonlyMap<string, Rgb>, name: string): Rgb => {
  const token = tokens.get(name);
  if (token === undefined) {
    throw new Error(`Missing required color token: ${name}`);
  }
  return token;
};

describe("accessibility color contracts", () => {
  it("keeps secondary text and control boundaries above their required contrast", () => {
    const stylesheet = fs.readFileSync(STYLES_PATH, "utf8");
    const tokens = new Map<string, Rgb>();
    for (const match of stylesheet.matchAll(TOKEN_PATTERN)) {
      const groups = match.groups;
      if (groups === undefined) {
        throw new Error("Color-token pattern must expose named groups.");
      }
      tokens.set(groups.name, toRgb(groups.value));
    }
    const background = requireToken(tokens, "app-bg");
    const subtle = requireToken(tokens, "app-subtle");
    const border = requireToken(tokens, "app-border");
    const surfaces = [background, requireToken(tokens, "app-surface"), toRgb("#ffffff")];

    for (const match of stylesheet.matchAll(WASH_PATTERN)) {
      const groups = match.groups;
      if (groups === undefined) {
        throw new Error("Gradient-wash pattern must expose named groups.");
      }
      surfaces.push(
        blend(
          [Number(groups.red), Number(groups.green), Number(groups.blue)],
          background,
          Number(groups.alpha),
        ),
      );
    }

    for (const surface of surfaces) {
      expect(contrastRatio(subtle, surface)).toBeGreaterThanOrEqual(4.5);
      expect(contrastRatio(border, surface)).toBeGreaterThanOrEqual(3);
    }
  });

  it("keeps every custom field focus border paired with a deterministic outline", () => {
    for (const sourcePath of FIELD_SOURCE_PATHS) {
      const focusBorderLines = fs
        .readFileSync(sourcePath, "utf8")
        .split(/\r?\n/)
        .filter((line) => line.includes("focus:border-[var(--app-accent)]"));

      expect(focusBorderLines.length).toBeGreaterThan(0);
      for (const line of focusBorderLines) {
        expect(line).toContain("focus-visible:outline-2");
        expect(line).toContain("focus-visible:outline-solid");
        expect(line).toContain("focus-visible:outline-offset-2");
        expect(line).toContain("focus-visible:outline-[var(--app-accent)]");
      }
    }
  });
});
