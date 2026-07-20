import { expect, test } from "@playwright/test";

test("Prospect can view the Tutor landing page while the service is live", async ({
  page,
}) => {
  const healthResponse = await page.request.get("/api/health");

  expect(healthResponse.status()).toBe(200);
  expect(await healthResponse.json()).toEqual({ status: "ok" });

  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Personal tutoring, thoughtfully planned." }),
  ).toBeVisible();
  await expect(page.getByText("Dev tools")).toHaveCount(0);
});

test("retired Invitation Claim browser route is unavailable", async ({ page }) => {
  await page.goto("/student/claim/confirm?token=retired-token");

  await expect(
    page.getByRole("heading", { name: "Personal tutoring, thoughtfully planned." }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Invitation Claim/ }),
  ).toHaveCount(0);
});

test("theme selection persists across application pages", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("contentinfo").getByRole("button", { name: "Dark mode" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  await page.goto("/sign-in");
  await expect(page.getByRole("contentinfo")).toBeVisible();
  await expect(page.getByRole("button", { name: "Light mode" })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
});

test("Prospect submits an Inquiry without leaving the landing page", async ({
  page,
}) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Request tutoring" }).click();
  await expect(
    page.getByRole("dialog", { name: "Request tutoring" }),
  ).toBeVisible();
  await page.getByLabel("Email address").fill("Prospect@Example.COM");
  await page
    .getByLabel("How can tutoring help?")
    .fill("I would like support with calculus.");
  await page.getByRole("button", { name: "Send request" }).click();

  await expect(
    page.getByText("Thanks. Your tutoring request has been received."),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/$/);
});

test("production preview applies the browser security baseline", async ({ page }) => {
  const response = await page.goto("/");

  expect(response).not.toBeNull();
  if (response === null) {
    return;
  }
  const headers = response.headers();

  expect(headers["content-security-policy"]).toBe(
    "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'",
  );
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  expect(headers["permissions-policy"]).toBe(
    "camera=(), geolocation=(), microphone=(), payment=()",
  );
});

test("service is ready on an isolated migrated schema", async ({ request }) => {
  const response = await request.get("/api/ready");

  expect(response.status()).toBe(200);
  expect(await response.json()).toEqual({ status: "ready" });
});
