import { expect, test } from "@playwright/test";

import { signInTutor } from "./helpers";

test("Tutor signs in through the development outbox and logs out", async ({
  page,
}) => {
  await page.goto("/tutor/sign-in");

  const accessSurface = page.locator("main.login-authentication");
  await expect(accessSurface).toBeVisible();
  await expect(page.getByText("© 2026 Tutoring Platform")).toBeVisible();
  const emailInput = page.getByLabel("Email address");
  await emailInput.fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  await expect(page.getByText("Check the development outbox")).toBeVisible();
  await expect(accessSurface).toBeVisible();

  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);

  await expect(
    page.getByRole("heading", { name: "Confirm Tutor sign-in" }),
  ).toBeVisible();
  await expect(accessSurface).toBeVisible();
  await expect(page.getByText("© 2026 Tutoring Platform")).toBeVisible();
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
  const navigation = page.getByRole("navigation", { name: "Tutor workspace" });
  await expect(navigation).toBeVisible();
  await expect(accessSurface).toHaveCount(0);
  await expect(navigation.getByRole("button")).toHaveCount(4);
  const overviewButton = navigation.getByRole("button", { name: "Overview" });
  const studentsButton = navigation.getByRole("button", { name: "Students & Calendar" });
  const availabilityButton = navigation.getByRole("button", { name: "Availability & Business" });
  const requestsButton = navigation.getByRole("button", { name: /Requests/ });
  await expect(overviewButton).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("region", { name: "Daily metrics" })).toBeVisible();

  await studentsButton.click();
  const studentsPanel = page.getByRole("region", { name: "Students & Calendar" });
  await expect(studentsPanel.getByRole("heading", { name: "Students" })).toBeVisible();
  await expect(studentsPanel.getByRole("heading", { name: "Weekly Booking Calendar" })).toBeVisible();

  await availabilityButton.click();
  const availabilityPanel = page.getByRole("region", { name: "Availability & Business" });
  await expect(studentsPanel).toHaveCount(0);
  await expect(availabilityPanel.getByRole("heading", { name: "Availability Calendar" })).toBeVisible();
  await expect(availabilityPanel.getByRole("heading", { name: "Business settings" })).toBeVisible();

  await requestsButton.click();
  const requestsPanel = page.getByRole("region", { name: "Requests", exact: true });
  await expect(availabilityPanel).toHaveCount(0);
  await expect(requestsPanel.getByRole("heading", { name: "Active Inquiries" })).toBeVisible();
  await expect(requestsPanel.getByRole("heading", { name: "Login Requests" })).toBeVisible();
  await expect(page.getByText("© 2026 Tutoring Platform")).toBeHidden();
  const themeToggle = page.getByRole("button", { name: "Dark mode" });
  await expect(themeToggle).toHaveAttribute("aria-pressed", "false");
  await themeToggle.click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("button", { name: "Light mode" })).toHaveAttribute("aria-pressed", "true");

  await availabilityButton.click();
  await expect(page.getByLabel("Tutor timezone")).toHaveValue("America/Chicago");
  await page.getByLabel("Tutor timezone").fill("America/New_York");
  await page
    .getByLabel("Default remote Meeting Details")
    .fill("https://meet.example.com/tutor");
  await page.getByRole("button", { name: "Save business settings" }).click();
  await expect(page.getByText("Business settings saved")).toBeVisible();

  await page.reload();
  await expect(page.getByRole("navigation", { name: "Tutor workspace" })).toBeVisible();
  await page.getByRole("button", { name: "Availability & Business" }).click();
  await expect(page.getByLabel("Tutor timezone")).toHaveValue("America/New_York");

  const availability = page.getByRole("form", { name: "Add Availability" });
  await availability.getByLabel("Weekday").selectOption("0");
  await availability.getByLabel("Start time").fill("09:00");
  await availability.getByLabel("End time").fill("11:30");
  await availability.getByRole("button", { name: "Add Availability" }).click();
  const monday = page.getByRole("article", { name: "Monday Availability" });
  await expect(monday).toBeVisible();
  await monday.getByLabel("Availability weekday").selectOption("1");
  await monday.getByRole("button", { name: "Save Availability" }).click();
  await page.reload();
  await page.getByRole("button", { name: "Availability & Business" }).click();
  const tuesday = page.getByRole("article", { name: "Tuesday Availability" });
  await expect(tuesday).toBeVisible();
  await tuesday.getByRole("button", { name: "Delete Availability" }).click();
  await expect(tuesday).toHaveCount(0);

  const blocked = page.getByRole("form", { name: "Add Blocked Time" });
  await blocked.getByLabel("Blocked start").fill("2026-07-20T10:00");
  await blocked.getByLabel("Blocked end").fill("2026-07-20T11:00");
  await blocked.getByLabel("Private blocked reason").fill("Private appointment");
  await blocked.getByRole("button", { name: "Add Blocked Time" }).click();
  const blockedRow = page.getByRole("article", { name: "Blocked Time" });
  await expect(blockedRow.getByLabel("Private blocked reason")).toHaveValue("Private appointment");
  await blockedRow.getByRole("button", { name: "Delete Blocked Time" }).click();
  await expect(blockedRow).toHaveCount(0);

  await page.getByRole("button", { name: "Log out" }).click();
  const logoutDialog = page.getByRole("dialog", { name: "Log out?" });
  await expect(logoutDialog).toContainText(
    "You’ll need to request a new Login Link to sign in again.",
  );
  await logoutDialog.getByRole("button", { name: "Stay signed in" }).click();
  await expect(logoutDialog).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Tutor workspace" })).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();
  await logoutDialog.getByRole("button", { name: "Log out" }).click();
  await expect(
    page.getByRole("heading", { name: "Personal tutoring, thoughtfully planned." }),
  ).toBeVisible();
  await expect(page).toHaveURL(/\/$/);
  expect((await page.request.get("/api/tutor/session")).status()).toBe(401);
  await expect(page.getByText("© 2026 Tutoring Platform")).toBeVisible();
});

test("authenticated roles stay on their own routes", async ({ browser, page }, testInfo) => {
  await signInTutor(page);
  await page.goto("/student", { waitUntil: "commit" });
  await expect(page).toHaveURL(/\/tutor$/);

  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();
  const invitation = page.getByLabel("Manual Invitation");
  await invitation.getByLabel("Invitee email").fill(`role-routing-${Date.now()}@example.com`);
  await invitation.getByRole("button", { name: "Create Invitation" }).click();

  const studentContext = await browser.newContext({ baseURL: testInfo.project.use.baseURL });
  const studentPage = await studentContext.newPage();
  await studentPage.goto(await invitation.getByLabel("Invitation link").inputValue());
  await studentPage.getByLabel("Display name").fill("Role Routing Student");
  await studentPage.getByRole("button", { name: "Create Account" }).click();
  await expect(studentPage.getByRole("heading", { name: "Student workspace" })).toBeVisible();
  await studentPage.goto("/tutor/sign-in", { waitUntil: "commit" });
  await expect(studentPage).toHaveURL(/\/student$/);
  await studentContext.close();
});

test("anonymous Student and unknown browser routes return home", async ({ page }) => {
  await page.goto("/student");
  await expect(page).toHaveURL(/\/$/);
  await expect(
    page.getByRole("heading", { name: "Personal tutoring, thoughtfully planned." }),
  ).toBeVisible();

  for (const path of [
    "/not-a-current-route",
    "/student/not-a-current-route",
    "/sign-in/not-a-current-route",
    "/tutor/not-a-current-route",
  ]) {
    await page.goto(path);
    await expect(page).toHaveURL(/\/$/);
  }

  await page.goto("/tutor/sign-in");
  await expect(page.getByRole("heading", { name: "Tutor sign-in" })).toBeVisible();
  await expect(page).toHaveURL(/\/tutor\/sign-in$/);
});

test("unknown session roles fail open without a redirect loop", async ({ page }) => {
  await page.route("**/api/auth/session", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ role: "admin" }) }),
  );

  await page.goto("/tutor/sign-in");

  await expect(page.getByRole("heading", { name: "Tutor sign-in" })).toBeVisible();
  await expect(page).toHaveURL(/\/tutor\/sign-in$/);
});

test("a Student token confirmed on the Tutor route lands in the Student workspace", async ({ browser, page }, testInfo) => {
  const email = `cross-role-confirm-${Date.now()}@example.com`;
  await signInTutor(page);
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();
  const invitation = page.getByLabel("Manual Invitation");
  await invitation.getByLabel("Invitee email").fill(email);
  await invitation.getByRole("button", { name: "Create Invitation" }).click();

  const studentContext = await browser.newContext({ baseURL: testInfo.project.use.baseURL });
  const studentPage = await studentContext.newPage();
  await studentPage.goto(await invitation.getByLabel("Invitation link").inputValue());
  await studentPage.getByLabel("Display name").fill("Cross Role Student");
  await studentPage.getByRole("button", { name: "Create Account" }).click();
  await expect(studentPage.getByRole("heading", { name: "Student workspace" })).toBeVisible();

  await studentPage.request.post("/api/auth/magic-links", { data: { email } });
  await page.reload();
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();
  const request = page.getByRole("article").filter({ hasText: email });
  await request.getByRole("button", { name: "Generate Login Link" }).click();
  const loginLink = await request.getByLabel("Login Link").inputValue();

  // The link is opened in a fresh browser, like a real email client handoff.
  const confirmContext = await browser.newContext({ baseURL: testInfo.project.use.baseURL });
  const confirmPage = await confirmContext.newPage();
  await confirmPage.goto(loginLink.replace("/sign-in/confirm", "/tutor/sign-in/confirm"));
  await confirmPage.getByRole("button", { name: "Confirm sign-in" }).click();

  await expect(confirmPage).toHaveURL(/\/student$/);
  await expect(confirmPage.getByRole("heading", { name: "Student workspace" })).toBeVisible();
  await confirmContext.close();
  await studentContext.close();
});

test("Tutor access surface keeps theme, focus, and responsive geometry", async ({
  page,
}) => {
  for (const theme of ["light", "dark"]) {
    await page.goto("/tutor/sign-in");
    await page.evaluate((value) => localStorage.setItem("theme", value), theme);
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);

    for (const width of [390, 800, 1280]) {
      await page.setViewportSize({ width, height: 800 });
      await expect(page.locator("main.login-authentication")).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
  }

  await page.keyboard.press("Tab");
  const emailInput = page.getByLabel("Email address");
  await expect(emailInput).toBeFocused();
  expect(await emailInput.evaluate((element) => getComputedStyle(element).boxShadow)).not.toBe("none");
});

test("Tutor reviews, archives, and confirms deletion of Inquiries", async ({
  page,
}) => {
  await page.request.post("/api/inquiries", {
    data: {
      email: "queue-prospect@example.com",
      message: "I need help with calculus.",
    },
  });
  await page.request.post("/api/inquiries", {
    data: {
      email: "invite-from-inquiry@example.com",
      message: "Please invite me after review.",
    },
  });
  await page.request.post("/api/inquiries", {
    data: {
      email: "spam@example.com",
      message: "Please remove this request.",
    },
  });
  await signInTutor(page);
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();

  const prospect = page.getByRole("article", {
    name: "queue-prospect@example.com",
  });
  await expect(prospect.getByText("I need help with calculus.")).toBeVisible();
  await prospect.getByRole("button", { name: "Archive" }).click();
  await expect(prospect).toHaveCount(0);

  page.once("dialog", (dialog) => dialog.accept());
  const spam = page.getByRole("article", { name: "spam@example.com" });
  await spam.getByRole("button", { name: "Delete permanently" }).click();
  await expect(spam).toHaveCount(0);

  const invite = page.getByRole("article", {
    name: "invite-from-inquiry@example.com",
  });
  await invite.getByRole("button", { name: "Create Invitation" }).click();
  await expect(invite.getByText("State: Invited")).toBeVisible();
  await expect(invite.getByLabel("Invitation link")).toHaveValue(/\/invite\//);
});

test("Tutor creates a retrievable manual Invitation in one action", async ({ page }) => {
  await signInTutor(page);
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();

  const manualInvitation = page.getByLabel("Manual Invitation");
  await manualInvitation.getByLabel("Invitee email").fill("Invitee@Example.COM");
  await manualInvitation.getByRole("button", { name: "Create Invitation" }).click();

  await expect(
    page.getByText("Created Invitation for invitee@example.com"),
  ).toBeVisible();
  await expect(manualInvitation.getByLabel("Invitation link")).toHaveValue(/\/invite\//);
});

test("Invitee opens a personalized setup page without the Private Tutor Note", async ({
  page,
}) => {
  await signInTutor(page);
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();

  const manualInvitation = page.getByLabel("Manual Invitation");
  await manualInvitation.getByLabel("Invitee email").fill("invitee@example.com");
  await manualInvitation.getByRole("button", { name: "Create Invitation" }).click();
  const invitationLink = await manualInvitation.getByLabel("Invitation link").inputValue();

  await page.goto(invitationLink);

  const invitationSurface = page.locator("main.login-authentication");
  await expect(invitationSurface).toBeVisible();
  await expect(page.getByLabel("Bound email")).toHaveValue(
    "invitee@example.com",
  );
  await expect(page.getByLabel("Bound email")).toBeEditable({ editable: false });

  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => localStorage.setItem("theme", value), theme);
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);

    for (const width of [390, 800, 1280]) {
      await page.setViewportSize({ width, height: 800 });
      await expect(invitationSurface).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
  }

  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  const displayName = page.getByLabel("Display name");
  await expect(displayName).toBeFocused();
  expect(await displayName.evaluate((element) => getComputedStyle(element).boxShadow)).not.toBe("none");
});

test("Invitation loading and unavailable states share the access surface", async ({
  page,
}) => {
  for (const theme of ["light", "dark"]) {
    await page.goto("/");
    await page.evaluate((value) => localStorage.setItem("theme", value), theme);
    let releaseResponse!: () => void;
    const heldResponse = new Promise<void>((resolve) => {
      releaseResponse = resolve;
    });
    const invitationRequest = `**/api/invitations/state-${theme}`;
    await page.route(invitationRequest, async (route) => {
      await heldResponse;
      await route.fulfill({ status: 404 });
    });

    await page.goto(`/invite/state-${theme}`);
    const invitationSurface = page.locator("main.login-authentication");
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    await expect(invitationSurface).toContainText("Loading Invitation…");
    releaseResponse();
    await expect(invitationSurface.getByRole("heading", {
      name: "Invitation unavailable",
    })).toBeVisible();
    await page.unroute(invitationRequest);
  }
});

test("Tutor corrects an active Invitation email", async ({ page }) => {
  await signInTutor(page);
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();
  const manualInvitation = page.getByLabel("Manual Invitation");
  await manualInvitation.getByLabel("Invitee email").fill("typo@example.com");
  await manualInvitation.getByRole("button", { name: "Create Invitation" }).click();

  await manualInvitation.getByLabel("Bound email").fill("corrected@example.com");
  await manualInvitation.getByRole("button", { name: "Correct email" }).click();

  await expect(page.getByLabel("Bound email")).toHaveValue(
    "corrected@example.com",
  );
  await expect(page.getByText("Email corrected")).toBeVisible();
});

test("Tutor regenerates and revokes an active Invitation", async ({ page }) => {
  await signInTutor(page);
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();
  const manualInvitation = page.getByLabel("Manual Invitation");
  await manualInvitation.getByLabel("Invitee email").fill("invitee@example.com");
  await manualInvitation.getByRole("button", { name: "Create Invitation" }).click();
  const priorLink = await manualInvitation.getByLabel("Invitation link").inputValue();

  await manualInvitation.getByRole("button", { name: "Regenerate Invitation" }).click();

  await expect(manualInvitation.getByLabel("Invitation link")).not.toHaveValue(priorLink);
  await expect(page.getByText("Replacement link shown once")).toBeVisible();

  await manualInvitation.getByRole("button", { name: "Revoke Invitation" }).click();

  await expect(
    page.getByRole("heading", { name: "Revoked Invitation for invitee@example.com" }),
  ).toBeVisible();
  await expect(manualInvitation.getByLabel("Invitation link")).toHaveCount(0);
});
