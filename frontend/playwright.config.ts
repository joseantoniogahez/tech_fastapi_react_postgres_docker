import { defineConfig, devices } from "@playwright/test";

const PORT = 4173;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const IS_CI_RUN = Boolean(process.env.CI) || process.env.npm_lifecycle_event === "test:e2e:ci";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: IS_CI_RUN,
  retries: 0,
  workers: IS_CI_RUN ? 1 : undefined,
  reporter: IS_CI_RUN ? [["line"]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 4173",
    url: BASE_URL,
    reuseExistingServer: !IS_CI_RUN,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
});
