import { defineConfig } from "@playwright/test";

const frontendOrigin = `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT ?? "7410"}`;
const backendOrigin = `http://127.0.0.1:${process.env.E2E_BACKEND_PORT ?? "7411"}`;
const developmentFrontendOrigin = `http://127.0.0.1:${process.env.E2E_DEVELOPMENT_FRONTEND_PORT ?? "7412"}`;

export default defineConfig({
  testDir: ".",
  fullyParallel: false,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: frontendOrigin,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "bun run serve:e2e:backend",
      url: `${backendOrigin}/api/ready`,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "bun run serve:e2e:frontend",
      url: frontendOrigin,
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: "bun run serve:e2e:development-frontend",
      url: developmentFrontendOrigin,
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
});
