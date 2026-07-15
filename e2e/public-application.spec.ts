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
});

test("public pages apply the browser security baseline", async ({ request }) => {
  const response = await request.get("/");
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
