import { expect, test } from "@playwright/test";

test("Tutor signs in through the development outbox and logs out", async ({
  page,
}) => {
  await page.goto("/tutor/sign-in");

  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  await expect(page.getByText("Check the development outbox")).toBeVisible();

  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);

  await expect(
    page.getByRole("heading", { name: "Confirm Tutor sign-in" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
  const navigation = page.getByRole("navigation", { name: "Tutor workspace" });
  await expect(navigation).toBeVisible();
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
  await expect(requestsPanel.getByRole("heading", { name: "Refund Requests" })).toBeVisible();
  await expect(page.getByText("© 2026 Tutoring Platform")).toHaveCount(0);
  const themeToggle = page.getByRole("button", { name: "Dark mode" });
  await expect(themeToggle).toHaveAttribute("aria-pressed", "false");
  await themeToggle.click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("button", { name: "Light mode" })).toHaveAttribute("aria-pressed", "true");

  await availabilityButton.click();
  await expect(page.getByLabel("Session price (USD)")).toHaveValue("75.00");
  await page.getByLabel("Session price (USD)").fill("82.50");
  await page.getByLabel("Tutor timezone").fill("America/New_York");
  await page
    .getByLabel("Default remote Meeting Details")
    .fill("https://meet.example.com/tutor");
  await page.getByRole("button", { name: "Save business settings" }).click();
  await expect(page.getByText("Business settings saved")).toBeVisible();

  await page.reload();
  await expect(page.getByRole("navigation", { name: "Tutor workspace" })).toBeVisible();
  await page.getByRole("button", { name: "Availability & Business" }).click();
  await expect(page.getByLabel("Session price (USD)")).toHaveValue("82.50");

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
  await expect(
    page.getByRole("heading", { name: "Tutor sign-in" }),
  ).toBeVisible();
  await expect(page.getByText("© 2026 Tutoring Platform")).toBeVisible();
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
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
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
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();

  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
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
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
  await page.getByRole("navigation", { name: "Tutor workspace" }).getByRole("button", { name: /Requests/ }).click();

  const manualInvitation = page.getByLabel("Manual Invitation");
  await manualInvitation.getByLabel("Invitee email").fill("invitee@example.com");
  await manualInvitation.getByRole("button", { name: "Create Invitation" }).click();
  const invitationLink = await manualInvitation.getByLabel("Invitation link").inputValue();

  await page.goto(invitationLink);

  await expect(page.getByLabel("Bound email")).toHaveValue(
    "invitee@example.com",
  );
  await expect(page.getByLabel("Bound email")).toBeEditable({ editable: false });
});

test("Tutor corrects an active Invitation email", async ({ page }) => {
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
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
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
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
