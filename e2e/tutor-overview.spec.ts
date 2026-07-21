import { expect, type Page, test } from "@playwright/test";

type TutorData = Record<string, unknown>;

async function stubTutorOverview(page: Page, overrides: TutorData = {}) {
  const bodies: TutorData = {
    "/api/tutor/session": {},
    "/api/tutor/settings": { tutor_timezone: "America/Chicago" },
    "/api/tutor/bookings": { bookings: [] },
    "/api/tutor/students": { students: [] },
    "/api/tutor/inquiries": { inquiries: [] },
    "/api/tutor/login-requests": { login_requests: [] },
    "/api/tutor/refund-requests": { refund_requests: [] },
    "/api/tutor/overrides": [],
    ...overrides,
  };
  await page.route("**/api/tutor/**", (route) => route.fulfill({ json: bodies[new URL(route.request().url()).pathname] }));
}

test("Tutor Overview aggregates local operational data", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-07-20T15:00:00Z"));
  await stubTutorOverview(page, {
    "/api/tutor/bookings": { bookings: [
      { id: "later", start_at: "2026-07-20T20:00:00Z", focus: "Polynomials", status: "upcoming", student: { display_name: "Sofia Patel" } },
      { id: "cancelled", start_at: "2026-07-20T16:00:00Z", focus: null, status: "cancelled", student: { display_name: "Noah Williams" } },
      { id: "past", start_at: "2026-07-20T14:00:00Z", focus: "Fractions", status: "completed", student: { display_name: "Avery Chen" } },
      { id: "next", start_at: "2026-07-20T17:00:00Z", focus: "Related rates", status: "upcoming", student: { display_name: "Maya Chen" } },
      { id: "sunday", start_at: "2026-07-26T17:00:00Z", focus: null, status: "upcoming", student: { display_name: "Eli Thompson" } },
      { id: "next-week", start_at: "2026-07-27T17:00:00Z", focus: null, status: "upcoming", student: { display_name: "Jordan Lee" } },
    ] },
    "/api/tutor/students": { students: [
      { id: "5", display_name: "Sofia Patel" },
      { id: "1", display_name: "Avery Chen" },
      { id: "4", display_name: "Noah Williams" },
      { id: "2", display_name: "Eli Thompson" },
      { id: "3", display_name: "Maya Chen" },
    ] },
    "/api/tutor/inquiries": { inquiries: [
      { id: "inquiry", email: "prospect@example.com", message: "Calculus help", status: "new" },
      { id: "invited", email: "invitee@example.com", message: "Algebra help", status: "invited" },
    ] },
    "/api/tutor/login-requests": { login_requests: [
      { id: "login", email: "student@example.com", status: "pending" },
      { id: "generated", email: "returning@example.com", status: "generated" },
    ] },
    "/api/tutor/refund-requests": { refund_requests: [
      { id: "refund", amount_cents: 7500, currency: "USD", status: "pending", student: { id: "1", display_name: "Avery Chen" } },
      { id: "refunded", amount_cents: 7500, currency: "USD", status: "refunded", student: { id: "2", display_name: "Eli Thompson" } },
    ] },
  });

  await page.goto("/tutor");
  await expect(page.getByRole("heading", { name: "Monday" })).toBeVisible();
  const metrics = page.getByRole("region", { name: "Daily metrics" });
  await expect(metrics.getByText("Sessions today").locator("..")).toContainText("3");
  await expect(metrics.getByText("Bookings this week").locator("..")).toContainText("4");
  await expect(metrics.getByText("Active Students").locator("..")).toContainText("5");
  await expect(metrics.getByText("Open requests").locator("..")).toContainText("3");

  const rows = page.locator(".booking-ledger > div");
  await expect(rows).toHaveCount(2);
  await expect(rows.nth(0)).toContainText("Maya Chen");
  await expect(rows.nth(1)).toContainText("Sofia Patel");
  await expect(page.locator(".overview-next")).toContainText("Maya Chen");
  await expect(page.locator(".overview-students li")).toHaveText(["Avery Chen", "Eli Thompson", "Maya Chen", "Noah Williams"]);
  await expect(page.locator(".overview-requests")).toContainText("New Inquiries1Pending Login Requests1Pending Refund Requests1");
  await expect(page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ })).toContainText("3");
  const requestBadge = page.getByLabel("3 open requests");
  await expect(requestBadge).toHaveCSS("background-color", "rgb(18, 34, 57)");
  await expect(requestBadge).toHaveCSS("border-top-color", "rgb(255, 255, 255)");
  await expect(requestBadge).toHaveCSS("color", "rgb(255, 255, 255)");
  await expect(requestBadge).toHaveCSS("align-items", "center");
  await expect(requestBadge).toHaveCSS("justify-items", "center");

  await page.getByRole("button", { name: "Open calendar" }).click();
  const studentsCalendar = page.getByRole("region", { name: "Students & Calendar" });
  await expect(studentsCalendar).toBeVisible();
  await expect(studentsCalendar.getByLabel("Search Students")).toHaveCSS("background-color", "rgb(255, 255, 255)");
  const studentButton = studentsCalendar.getByRole("button", { name: "Sofia Patel", exact: true });
  await expect(studentButton).toHaveCSS("background-color", "rgb(18, 34, 57)");
  await expect(studentButton).toHaveCSS("border-top-color", "rgb(18, 34, 57)");
  await expect(studentButton).toHaveCSS("border-radius", "0px");
  await page.getByRole("button", { name: "Overview" }).click();
  await page.getByRole("button", { name: "3 open", exact: true }).click();
  await expect(page.getByRole("region", { name: "Requests", exact: true })).toBeVisible();
});

test("Tutor Overview shows empty states without overflow across themes and widths", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-07-20T15:00:00Z"));
  await stubTutorOverview(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/tutor");

  await expect(page.locator(".tutor-workspace")).toHaveCSS("background-image", /radial-gradient/);
  await expect(page.getByText("No more Bookings today.")).toBeVisible();
  await expect(page.getByText("No upcoming Bookings.")).toBeVisible();
  await expect(page.getByText("No open requests.")).toBeVisible();
  await expect(page.getByText("No Students yet.")).toBeVisible();
  const navigation = page.getByRole("navigation", { name: "Tutor workspace" });
  await expect(navigation.getByRole("button")).toHaveCount(4);
  for (const width of [390, 800, 1280]) {
    await page.setViewportSize({ width, height: 844 });
    await expect(navigation).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }

  await page.getByRole("button", { name: "Dark mode" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.getByRole("button", { name: "Students & Calendar" }).click();
  await expect(page.getByLabel("Search Students")).toHaveCSS("background-color", "rgb(16, 39, 65)");
  await page.getByRole("button", { name: "Requests" }).click();
  const invitationButton = page.getByRole("button", { name: "Create Invitation" });
  await expect(invitationButton).toHaveCSS("background-color", "rgb(23, 30, 43)");
  await expect(invitationButton).toHaveCSS("border-top-color", "rgb(255, 255, 255)");
  await expect(invitationButton).toHaveCSS("color", "rgb(255, 255, 255)");
  await page.getByRole("button", { name: "Overview" }).click();
  for (const width of [1280, 800, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await expect(page.locator(".tutor-overview-grid")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
});

test("Tutor Overview retries a failed request", async ({ page }) => {
  let settingsAttempts = 0;
  await page.route("**/api/tutor/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/tutor/settings" && settingsAttempts++ === 0) return route.fulfill({ status: 500 });
    const bodies: TutorData = {
      "/api/tutor/session": {},
      "/api/tutor/settings": { tutor_timezone: "America/Chicago" },
      "/api/tutor/bookings": { bookings: [] },
      "/api/tutor/students": { students: [] },
      "/api/tutor/inquiries": { inquiries: [] },
      "/api/tutor/login-requests": { login_requests: [] },
      "/api/tutor/refund-requests": { refund_requests: [] },
      "/api/tutor/overrides": [],
    };
    return route.fulfill({ json: bodies[path] });
  });

  await page.goto("/tutor");
  await expect(page.getByRole("alert")).toContainText("Could not load the overview.");
  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByRole("region", { name: "Daily metrics" })).toBeVisible();
});
