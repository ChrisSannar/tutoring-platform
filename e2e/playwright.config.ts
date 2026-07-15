import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  fullyParallel: false,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:7310",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "bun run serve:backend",
      url: "http://127.0.0.1:7311/api/ready",
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "bun run serve:frontend",
      url: "http://127.0.0.1:7310",
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
