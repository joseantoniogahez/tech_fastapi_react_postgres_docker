import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    minify: "terser",
    terserOptions: {
      compress: {
        passes: 2,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
    css: true,
    exclude: ["e2e/**", "**/node_modules/**", "**/dist/**", "**/.{idea,git,cache,output,temp}/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      thresholds: {
        statements: 92,
        branches: 85,
        functions: 96,
        lines: 92,
      },
    },
  },
});
