import { expect, test } from "@playwright/test";

const developmentFrontendOrigin = `http://127.0.0.1:${process.env.E2E_DEVELOPMENT_FRONTEND_PORT ?? "7412"}`;

test("documented Vite development startup renders the Tutor landing page", async ({
  page,
}) => {
  await page.goto(developmentFrontendOrigin);

  await expect(
    page.getByRole("heading", { name: "Personal tutoring, thoughtfully planned." }),
  ).toBeVisible();
});
