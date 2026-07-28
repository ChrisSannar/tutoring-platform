import { expect, test } from "@playwright/test";

import { signInTutor } from "./helpers";

test("Login states keep Constellation hierarchy without overflow", async ({
  page,
}) => {
  await page.goto("/sign-in");

  const login = page.locator(".login-authentication");
  const email = page.getByLabel("Email address");
  await expect(login).toHaveCSS("background-color", "rgba(250, 252, 255, 0.94)");
  await email.focus();
  await expect(email).toHaveCSS("border-color", "rgb(20, 108, 255)");
  for (const width of [390, 800, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
  }

  await page.getByRole("button", { name: "Dark mode" }).click();
  await expect(login).toHaveCSS("background-color", "rgba(11, 25, 43, 0.94)");
  await email.fill("unknown@example.com");
  await page.getByRole("button", { name: "Request Login Link" }).click();
  await expect(
    page.getByRole("heading", { name: "Login Request received" }),
  ).toBeVisible();

  await page.goto("/sign-in/confirm?token=invalid");
  const confirm = page.getByRole("button", { name: "Confirm sign-in" });
  await confirm.focus();
  await expect(confirm).toHaveCSS("outline-color", "rgb(156, 188, 255)");
  await confirm.click();
  await expect(
    page.getByRole("heading", { name: "Login Link unavailable" }),
  ).toBeVisible();
});

test("returning Student receives a Tutor-generated Login Link", async ({ browser, page }, testInfo) => {
  await signInTutor(page);
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();

  const invitation = page.getByLabel("Manual Invitation");
  await invitation.getByLabel("Invitee email").fill("returning@example.com");
  await invitation.getByRole("button", { name: "Create Invitation" }).click();
  await page.goto(await invitation.getByLabel("Invitation link").inputValue());
  await page.getByLabel("Display name").fill("Returning Student");
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page.getByRole("heading", { name: "Student workspace" })).toBeVisible();

  const publicContext = await browser.newContext({ baseURL: testInfo.project.use.baseURL });
  const publicPage = await publicContext.newPage();
  await publicPage.goto("/");
  await publicPage.getByRole("button", { name: "I’m already a student" }).click();
  const loginDialog = publicPage.getByRole("dialog", { name: "Request a Login Link" });
  await loginDialog.getByLabel("Email address").fill("returning@example.com");
  await loginDialog.getByRole("button", { name: "Request Login Link" }).click();
  await expect(publicPage.getByRole("heading", { name: "Login Request received" })).toBeVisible();

  await signInTutor(page);
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();
  const request = page.getByRole("article").filter({ hasText: "returning@example.com" });
  await request.getByRole("button", { name: "Generate Login Link" }).click();
  const loginLink = await request.getByLabel("Login Link").inputValue();

  await publicPage.goto(loginLink);
  await publicPage.getByRole("button", { name: "Confirm sign-in" }).click();
  await expect(publicPage.getByRole("heading", { name: "Student workspace" })).toBeVisible();
  await publicPage.goto("/");
  await expect(publicPage).toHaveURL(/\/student$/);
  await publicContext.close();
});
