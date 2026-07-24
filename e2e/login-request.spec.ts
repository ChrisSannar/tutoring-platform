import { expect, test } from "@playwright/test";

import { signInTutor } from "./helpers";

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
  await publicPage.getByRole("link", { name: "Log In" }).click();
  await publicPage.getByLabel("Email address").fill("returning@example.com");
  await publicPage.getByRole("button", { name: "Request Login Link" }).click();
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
  await expect(publicPage.getByRole("link", { name: "Dashboard" })).toBeVisible();
  await publicContext.close();
});
