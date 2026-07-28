import { expect, test } from "@playwright/test";

import { signInTutor } from "./helpers";

test("Checkout states keep Constellation hierarchy without overflow", async ({ page }) => {
  let releaseCheckout!: () => void;
  await page.route("**/api/student/checkouts/checkout-test", async (route) => {
    await new Promise<void>((resolve) => { releaseCheckout = resolve; });
    await route.fulfill({
      json: {
        checkout_session_id: "checkout-test",
        checkout_url: "/checkout/fake/checkout-test",
        amount_cents: 12500,
        currency: "USD",
        status: "pending",
      },
    });
  });

  await page.goto("/checkout/fake/checkout-test");
  const checkout = page.locator(".login-authentication");
  await expect(page.getByText("Loading checkout status…")).toBeVisible();
  await expect.poll(() => typeof releaseCheckout).toBe("function");
  releaseCheckout();

  await expect(page.getByRole("heading", { name: "Test Checkout" })).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("Status: pending");
  await expect(checkout).toHaveCSS("background-color", "rgba(250, 252, 255, 0.94)");
  const returnLink = page.getByRole("link", { name: "Return to tutoring platform" });
  await expect(returnLink).toHaveAttribute("href", "/checkout/return?session_id=checkout-test");
  await returnLink.focus();
  await expect(returnLink).toHaveCSS("outline-color", "rgb(20, 108, 255)");
  for (const width of [390, 800, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }

  await page.getByRole("button", { name: "Dark mode" }).click();
  await expect(checkout).toHaveCSS("background-color", "rgba(11, 25, 43, 0.94)");
  for (const width of [1280, 800, 390]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }

  await page.goto("/checkout/return");
  await expect(page.getByRole("heading", { name: "Checkout unavailable" })).toBeVisible();
  await expect(page.locator(".login-authentication")).toBeVisible();
});

test("Inquiry becomes a promotion-funded lesson with a published note", async ({ browser, page, playwright }, testInfo) => {
  test.setTimeout(60_000);
  const origin = testInfo.project.use.baseURL;
  if (!origin) throw new Error("Playwright baseURL must be configured");

  await page.goto("/");
  await page.getByRole("button", { name: "Request tutoring" }).click();
  await page.getByLabel("Email address").fill("critical@example.com");
  await page.getByLabel("How can tutoring help?").fill("I need help understanding quadratic equations.");
  await page.getByRole("button", { name: "Send request" }).click();
  await expect(page.getByText("Thanks. Your tutoring request has been received.")).toBeVisible();

  const tutorContext = await browser.newContext({ baseURL: origin });
  const tutorPage = await tutorContext.newPage();
  const tutorCsrf = await signInTutor(tutorPage);
  const setClock = (now: string) => tutorPage.evaluate(async ({ newNow, csrf }) => {
    const response = await fetch("/api/testing/clock", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: JSON.stringify({ now: newNow }),
    });
    return response.status;
  }, { newNow: now, csrf: tutorCsrf });
  expect(await setClock("2026-07-19T08:00:00Z")).toBe(200);

  await tutorPage.getByRole("button", { name: "Availability & Business" }).click();
  const availability = tutorPage.getByRole("form", { name: "Add Availability" });
  await availability.getByLabel("Weekday").selectOption("2");
  await availability.getByLabel("Start time").fill("09:00");
  await availability.getByLabel("End time").fill("11:00");
  await availability.getByRole("button", { name: "Add Availability" }).click();

  await tutorPage.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();
  const inquiry = tutorPage.getByRole("article", { name: "critical@example.com" });
  await inquiry.getByRole("button", { name: "Create Invitation" }).click();
  const invitationLink = await inquiry.getByLabel("Invitation link").inputValue();
  expect(invitationLink).toMatch(/^\/invite\//);
  const token = invitationLink.split("/").at(-1)!;

  const scanner = await playwright.request.newContext({ baseURL: origin });
  expect((await scanner.get(`/api/invitations/${token}`)).status()).toBe(200);
  const beforeClaim = await tutorPage.evaluate(() => fetch("/api/tutor/students").then((response) => response.json()));
  expect(beforeClaim.students).toEqual([]);
  await scanner.dispose();

  await page.goto(invitationLink);
  await expect(page.getByLabel("Bound email")).toHaveValue("critical@example.com");
  await page.getByLabel("Display name").fill("Avery Critical");
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page.getByRole("heading", { name: "Student workspace" })).toBeVisible();

  const studentWorkspace = page.locator(".student-workspace");
  const studentWorkAreas = page.locator(".student-dashboard-grid > div > section");
  await expect(studentWorkspace).toHaveCSS("background-image", /radial-gradient/);
  await expect(studentWorkAreas).toHaveCount(2);
  await expect(studentWorkAreas.first()).toHaveCSS("background-color", "rgba(250, 252, 255, 0.94)");
  const slots = page.getByRole("region", { name: "Bookable Slots" });
  const firstSlot = slots.getByRole("button").first();
  await firstSlot.focus();
  await expect(firstSlot).toHaveCSS("outline-color", "rgb(20, 108, 255)");
  for (const width of [390, 800, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await page.getByRole("button", { name: "Dark mode" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(studentWorkAreas.first()).toHaveCSS("background-color", "rgba(11, 25, 43, 0.94)");
  for (const width of [1280, 800, 390]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await firstSlot.click();
  await expect(page.getByText("Funding: First Session Promotion")).toBeVisible();
  await page.getByLabel("Optional Booking Focus").fill("Quadratic equations");
  await page.getByRole("button", { name: "Schedule session" }).click();
  await expect(page.getByRole("heading", { name: "Upcoming Booking" })).toBeVisible();

  await tutorPage.reload();
  await tutorPage.getByRole("button", { name: "Students & Calendar" }).click();
  const calendar = tutorPage.getByRole("region", { name: "Weekly Booking Calendar", exact: true });
  await expect(calendar.getByRole("button", { name: /Avery Critical —/ })).toBeVisible();
  expect(await setClock("2026-07-22T16:00:01Z")).toBe(200);
  const studentsAfterClaim = await tutorPage.evaluate(() => fetch("/api/tutor/students").then((response) => response.json()));
  const studentId = studentsAfterClaim.students.find((student: { email: string }) => student.email === "critical@example.com").id;
  const noteWorkspace = await tutorPage.evaluate((id) => fetch(`/api/tutor/students/${id}/lesson-note-workspace`).then((response) => response.json()), studentId);
  expect(noteWorkspace).toHaveLength(1);
  await tutorPage.reload();
  await tutorPage.getByRole("button", { name: "Students & Calendar" }).click();
  await tutorPage.getByRole("button", { name: "Avery Critical", exact: true }).click();
  const detail = tutorPage.getByRole("dialog", { name: "Student Detail" });
  await expect(detail.getByLabel("Lesson Note title")).toBeVisible();
  await detail.getByLabel("Lesson Note title").fill("Quadratics review");
  await detail.getByLabel("Markdown source").fill("# Key idea\n- Factor before solving");
  await detail.getByRole("button", { name: "Save Draft" }).click();
  await detail.getByRole("button", { name: "Publish Lesson Note" }).click();
  await expect(detail.getByText("Status: published")).toBeVisible();

  await page.reload();
  const note = page.getByText(/Quadratics review/);
  await note.click();
  await expect(page.getByText("Factor before solving")).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download original Markdown" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain("quadratics-review.md");
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible();

  await tutorContext.close();
});
