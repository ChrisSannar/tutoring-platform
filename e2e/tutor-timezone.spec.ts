import { expect, test, type Browser, type Page } from "@playwright/test";

async function signInTutor(browser: Browser, origin: string) {
  const context = await browser.newContext({ baseURL: origin, timezoneId: "Asia/Tokyo" });
  const page = await context.newPage();
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outbox = await (await page.request.get("/api/development/outbox")).json();
  await page.goto(outbox.messages.at(-1).magic_link);
  const confirmation = page.waitForResponse((response) => response.url().includes("/api/auth/magic-links/confirm"));
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
  const csrfToken = (await (await confirmation).json()).csrf_token as string;
  return { context, page, csrfToken };
}

async function tutorMutation<T>(page: Page, csrfToken: string, path: string, body: unknown): Promise<T> {
  return page.evaluate(async ({ csrfToken, path, body }) => {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken, "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`${path} returned ${response.status}`);
    return response.json();
  }, { csrfToken, path, body });
}

test("Tutor scheduling uses the Tutor Timezone in a browser with a different timezone", async ({ browser }, testInfo) => {
  const origin = testInfo.project.use.baseURL;
  if (!origin) throw new Error("Playwright baseURL must be configured");
  const { context, page, csrfToken } = await signInTutor(browser, origin);

  await page.evaluate(async (csrfToken) => {
    const response = await fetch("/api/tutor/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: JSON.stringify({ currency: "USD", session_price_cents: 7500, tutor_timezone: "America/New_York", default_meeting_details: null }),
    });
    if (!response.ok) throw new Error(`settings returned ${response.status}`);
  }, csrfToken);
  await page.evaluate(async (csrfToken) => {
    const response = await fetch("/api/testing/clock", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
      body: JSON.stringify({ now: "2026-10-25T12:00:00Z" }),
    });
    if (!response.ok) throw new Error(`clock returned ${response.status}`);
  }, csrfToken);

  await tutorMutation(page, csrfToken, "/api/tutor/availability-windows", { weekday: 0, start_time: "10:00", end_time: "12:00" });
  const invitation = await tutorMutation<{ invitation_url: string }>(page, csrfToken, "/api/tutor/invitations", { email: "timezone-student@example.com" });
  const studentContext = await browser.newContext({ baseURL: origin });
  const studentPage = await studentContext.newPage();
  await studentPage.goto(invitation.invitation_url);
  await studentPage.getByLabel("Display name").fill("Timezone Student");
  await studentPage.getByRole("button", { name: "Create Account" }).click();

  const students = await page.evaluate(() => fetch("/api/tutor/students").then((response) => response.json()));
  const studentId = students.students.find((student: { email: string }) => student.email === "timezone-student@example.com").id;
  await tutorMutation(page, csrfToken, `/api/tutor/students/${studentId}/bookings`, {
    start_at: "2026-11-02T15:00:00Z",
    focus: null,
    complimentary: true,
  });

  await page.reload();
  const calendar = page.getByRole("region", { name: "Weekly Booking Calendar", exact: true });
  const booking = calendar.getByRole("button", { name: /Timezone Student/ });
  await expect(booking).toContainText("11/2/2026, 10:00:00 AM");
  const losAngelesContext = await browser.newContext({
    baseURL: origin,
    storageState: await context.storageState(),
    timezoneId: "America/Los_Angeles",
  });
  const losAngelesPage = await losAngelesContext.newPage();
  await losAngelesPage.goto("/tutor");
  await expect(losAngelesPage.getByRole("region", { name: "Weekly Booking Calendar", exact: true }).getByRole("button", { name: /Timezone Student/ })).toContainText("11/2/2026, 10:00:00 AM");

  await booking.click();
  await calendar.getByLabel("Move Booking").fill("2026-11-09T10:00");
  const moved = page.waitForResponse((response) => response.url().includes("/schedule") && response.request().method() === "PUT");
  await calendar.getByRole("button", { name: "Move Booking" }).click();
  expect((await (await moved).json()).start_at).toBe("2026-11-09T15:00:00Z");
  await expect(calendar.getByLabel("Move Booking")).toHaveValue("2026-11-09T10:00");

  const blockedForm = page.getByRole("form", { name: "Add Blocked Time" });
  await blockedForm.getByLabel("Blocked start").fill("2027-03-15T10:00");
  await blockedForm.getByLabel("Blocked end").fill("2027-03-15T11:00");
  await blockedForm.getByLabel("Private blocked reason").fill("DST boundary appointment");
  const blockedCreated = page.waitForResponse((response) => response.url().endsWith("/api/tutor/blocked-times") && response.request().method() === "POST");
  await blockedForm.getByRole("button", { name: "Add Blocked Time" }).click();
  expect((await (await blockedCreated).json()).start_at).toBe("2027-03-15T14:00:00Z");

  const blockedRow = page.getByRole("article", { name: "Blocked Time" });
  await expect(blockedRow.getByLabel("Blocked start")).toHaveValue("2027-03-15T10:00");
  await blockedRow.getByLabel("Blocked start").fill("2027-03-16T10:00");
  await blockedRow.getByLabel("Blocked end").fill("2027-03-16T11:00");
  const blockedSaved = page.waitForResponse((response) => response.url().includes("/api/tutor/blocked-times/") && response.request().method() === "PUT");
  await blockedRow.getByRole("button", { name: "Save Blocked Time" }).click();
  expect((await (await blockedSaved).json()).start_at).toBe("2027-03-16T14:00:00Z");

  const overrideForm = page.getByRole("form", { name: "Add Tutor Override" });
  await overrideForm.getByLabel("Override start").fill("2027-03-14T02:30");
  await overrideForm.getByLabel("Override warning").fill("Nonexistent spring-gap exception");
  await overrideForm.getByRole("button", { name: "Add Tutor Override" }).click();
  await expect(overrideForm.getByRole("alert")).toHaveText("Tutor wall time does not exist in the configured Tutor Timezone");
  await expect(page.getByRole("article", { name: "Tutor Override" })).toHaveCount(0);

  await overrideForm.getByLabel("Override start").fill("2027-03-15T12:00");
  await overrideForm.getByLabel("Override warning").fill("DST boundary exception");
  const overrideCreated = page.waitForResponse((response) => response.url().endsWith("/api/tutor/overrides") && response.request().method() === "POST");
  await overrideForm.getByRole("button", { name: "Add Tutor Override" }).click();
  const createdOverride = await (await overrideCreated).json();
  expect(createdOverride.start_at).toBe("2027-03-15T16:00:00Z");

  const overrideRow = page.getByRole("article", { name: "Tutor Override" });
  await expect(overrideRow.getByLabel("Override start")).toHaveValue("2027-03-15T12:00");
  await overrideRow.getByLabel("Override start").fill("2027-03-16T12:00");
  await overrideRow.getByLabel("Override warning").fill("Updated DST boundary exception");
  const overrideSaved = page.waitForResponse((response) => response.url().includes("/api/tutor/overrides/") && response.request().method() === "PUT");
  await overrideRow.getByRole("button", { name: "Save Tutor Override" }).click();
  const updatedOverride = await (await overrideSaved).json();
  expect(updatedOverride.start_at).toBe("2027-03-16T16:00:00Z");

  await page.reload();
  await booking.click();
  await calendar.getByLabel("Tutor Override").selectOption(createdOverride.id);
  await expect(calendar.getByLabel("Move Booking")).toHaveValue("2027-03-16T12:00");
  await calendar.getByLabel("I acknowledge: Updated DST boundary exception").check();
  const overrideMove = page.waitForResponse((response) => response.url().includes("/schedule") && response.request().method() === "PUT");
  await calendar.getByRole("button", { name: "Move Booking" }).click();
  expect((await (await overrideMove).json()).start_at).toBe("2027-03-16T16:00:00Z");

  const complimentaryInvitation = await tutorMutation<{ invitation_url: string }>(page, csrfToken, "/api/tutor/invitations", { email: "complimentary-timezone@example.com" });
  const complimentaryContext = await browser.newContext({ baseURL: origin });
  const complimentaryPage = await complimentaryContext.newPage();
  await complimentaryPage.goto(complimentaryInvitation.invitation_url);
  await complimentaryPage.getByLabel("Display name").fill("Complimentary Student");
  await complimentaryPage.getByRole("button", { name: "Create Account" }).click();
  await page.reload();
  await page.getByRole("button", { name: "Complimentary Student", exact: true }).click();
  const studentDetail = page.getByRole("dialog", { name: "Student Detail" });
  await studentDetail.getByLabel("Complimentary Booking start").fill("2026-11-16T10:00");
  const complimentaryCreated = page.waitForResponse((response) => response.url().includes("/api/tutor/students/") && response.url().endsWith("/bookings") && response.request().method() === "POST");
  await studentDetail.getByRole("button", { name: "Create Complimentary Booking" }).click();
  expect((await (await complimentaryCreated).json()).start_at).toBe("2026-11-16T15:00:00Z");

  await complimentaryContext.close();
  await losAngelesContext.close();
  await studentContext.close();
  await context.close();
});
