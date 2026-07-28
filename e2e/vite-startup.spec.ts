import { expect, test } from "@playwright/test";

const developmentFrontendOrigin = `http://127.0.0.1:${process.env.E2E_DEVELOPMENT_FRONTEND_PORT ?? "7412"}`;

test("development startup renders the landing page and route menu", async ({
  page,
}) => {
  await page.goto(developmentFrontendOrigin);

  await expect(
    page.getByRole("heading", { name: "Personal tutoring, thoughtfully planned." }),
  ).toBeVisible();

  await page.getByText("Dev tools").click();
  await page.getByLabel("Route").selectOption("/sign-in");

  await expect(page).toHaveURL(`${developmentFrontendOrigin}/sign-in`);
  await expect(page.getByRole("heading", { name: "Log In" })).toBeVisible();
});
