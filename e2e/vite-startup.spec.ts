import { expect, test } from "@playwright/test";

const developmentFrontendOrigin = `http://127.0.0.1:${process.env.E2E_DEVELOPMENT_FRONTEND_PORT ?? "7412"}`;
const frontendOrigin = `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT ?? "7410"}`;

test("development startup renders the landing page and route menu", async ({
  page,
}) => {
  await page.goto(developmentFrontendOrigin);

  await expect(
    page.getByRole("heading", { name: "Personal tutoring, thoughtfully planned." }),
  ).toBeVisible();

  await page.getByText("Dev tools").click();
  const moveDown = page.getByRole("button", { name: "Move dev tools to bottom" });
  const moveLeft = page.getByRole("button", { name: "Move dev tools to left" });
  await moveDown.click();
  await moveLeft.click();
  await expect(page.getByRole("button", { name: "Move dev tools to top" })).toHaveText("↑");
  await expect(page.getByRole("button", { name: "Move dev tools to right" })).toHaveText("→");
  await expect(page.locator("details.dev-tools")).toHaveCSS("bottom", "16px");
  await expect(page.locator("details.dev-tools")).toHaveCSS("left", "16px");
  await page.getByLabel("Route").selectOption("/sign-in");

  await expect(page).toHaveURL(`${developmentFrontendOrigin}/sign-in`);
  await expect(page.getByRole("heading", { name: "Log In" })).toBeVisible();
  await expect(page.locator("details.dev-tools")).toHaveAttribute("open", "");
  await expect(page.locator("details.dev-tools")).toHaveCSS("bottom", "16px");
  await expect(page.locator("details.dev-tools")).toHaveCSS("left", "16px");
});

test("development route menu creates a valid confirmation URL", async ({ page }) => {
  await page.route("**/api/auth/magic-links", (route) => route.fulfill({ json: {} }));
  await page.route("**/api/development/outbox", (route) => route.fulfill({
    json: { messages: [{ to: "tutor@example.com", magic_link: "/tutor/sign-in/confirm?token=real-dev-token" }] },
  }));
  await page.goto(developmentFrontendOrigin);
  await page.getByText("Dev tools").click();
  await page.getByLabel("Route").selectOption("/tutor/sign-in/confirm?token=dev-token");
  await expect(page).toHaveURL(`${developmentFrontendOrigin}/tutor/sign-in/confirm?token=real-dev-token`);
});

test("development Session controls log Tutor and Student sessions in and out", async ({ page }) => {
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    if (request.method() === "GET") return route.continue();
    await route.continue({ headers: { ...request.headers(), origin: frontendOrigin } });
  });

  await page.goto(developmentFrontendOrigin);
  await page.getByText("Dev tools").click();
  await page.getByRole("button", { name: "Log in tutor", exact: true }).click();
  await expect(page).toHaveURL(`${developmentFrontendOrigin}/tutor`);
  await expect(page.getByRole("navigation", { name: "Tutor workspace" })).toBeVisible();

  await page.getByRole("button", { name: "Log out tutor", exact: true }).click();
  await expect(page).toHaveURL(`${developmentFrontendOrigin}/tutor/sign-in`);
  expect((await page.request.get(`${developmentFrontendOrigin}/api/tutor/session`)).status()).toBe(401);

  await page.getByRole("button", { name: "Log in Student", exact: true }).click();
  await expect(page).toHaveURL(`${developmentFrontendOrigin}/student`);
  await expect(page.getByRole("heading", { name: "Student workspace" })).toBeVisible();

  await page.getByRole("button", { name: "Log out Student", exact: true }).click();
  await expect(page).toHaveURL(`${developmentFrontendOrigin}/sign-in`);
  expect((await page.request.get(`${developmentFrontendOrigin}/api/student/session`)).status()).toBe(401);
});
