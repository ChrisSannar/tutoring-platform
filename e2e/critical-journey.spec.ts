import { expect, test } from "@playwright/test";

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
  await tutorPage.goto("/tutor/sign-in");
  await tutorPage.getByLabel("Email address").fill("tutor@example.com");
  await tutorPage.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outbox = await (await tutorPage.request.get("/api/development/outbox")).json();
  await tutorPage.goto(outbox.messages.at(-1).magic_link);
  const confirmation = tutorPage.waitForResponse((response) => response.url().includes("/api/auth/magic-links/confirm"));
  await tutorPage.getByRole("button", { name: "Confirm sign-in" }).click();
  const tutorCsrf = (await (await confirmation).json()).csrf_token;
  const setClock = (now: string) => tutorPage.evaluate(async ({ newNow, csrf }) => {
    const response = await fetch("/api/testing/clock", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: JSON.stringify({ now: newNow }),
    });
    return response.status;
  }, { newNow: now, csrf: tutorCsrf });
  expect(await setClock("2026-07-19T08:00:00Z")).toBe(200);

  await tutorPage.getByRole("tab", { name: "Availability & Business" }).click();
  const availability = tutorPage.getByRole("form", { name: "Add Availability" });
  await availability.getByLabel("Weekday").selectOption("2");
  await availability.getByLabel("Start time").fill("09:00");
  await availability.getByLabel("End time").fill("11:00");
  await availability.getByRole("button", { name: "Add Availability" }).click();

  await tutorPage.getByRole("tab", { name: "Requests", exact: true }).click();
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

  const slots = page.getByRole("region", { name: "Bookable Slots" });
  await slots.getByRole("button").first().click();
  await expect(page.getByText("Funding: First Session Promotion")).toBeVisible();
  await page.getByLabel("Optional Booking Focus").fill("Quadratic equations");
  await page.getByRole("button", { name: "Schedule session" }).click();
  await expect(page.getByRole("heading", { name: "Upcoming Booking" })).toBeVisible();

  await tutorPage.reload();
  const calendar = tutorPage.getByRole("region", { name: "Weekly Booking Calendar", exact: true });
  await expect(calendar.getByRole("button", { name: /Avery Critical —/ })).toBeVisible();
  expect(await setClock("2026-07-22T16:00:01Z")).toBe(200);
  const studentsAfterClaim = await tutorPage.evaluate(() => fetch("/api/tutor/students").then((response) => response.json()));
  const studentId = studentsAfterClaim.students.find((student: { email: string }) => student.email === "critical@example.com").id;
  const noteWorkspace = await tutorPage.evaluate((id) => fetch(`/api/tutor/students/${id}/lesson-note-workspace`).then((response) => response.json()), studentId);
  expect(noteWorkspace).toHaveLength(1);
  await tutorPage.reload();
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
