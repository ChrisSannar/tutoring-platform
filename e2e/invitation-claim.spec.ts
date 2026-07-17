import { expect, test } from "@playwright/test";

test("Invitee confirms an Invitation Claim and continues as a Student", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "Personal tutoring, thoughtfully planned.",
    }),
  ).toBeVisible();

  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const tutorOutboxResponse = await page.request.get("/api/development/outbox");
  const tutorOutbox = await tutorOutboxResponse.json();
  await page.goto(tutorOutbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();

  const availability = page.getByRole("form", { name: "Add Availability" });
  await availability.getByLabel("Weekday").selectOption("4");
  await availability.getByLabel("Start time").fill("09:00");
  await availability.getByLabel("End time").fill("10:00");
  await availability.getByRole("button", { name: "Add Availability" }).click();

  const manualInvitation = page.getByLabel("Manual Invitation");
  await manualInvitation.getByLabel("Invitee email").fill("invitee@example.com");
  await manualInvitation.getByRole("button", { name: "Create Invitation" }).click();
  const invitationLink = await manualInvitation.getByLabel("Invitation link").inputValue();

  await page.goto(invitationLink);

  await expect(page.getByLabel("Bound email")).toHaveValue(
    "invitee@example.com",
  );
  await expect(page.getByLabel("Bound email")).toBeEditable({ editable: false });
  await page.getByLabel("Display name").fill("Avery Chen");
  await page.getByRole("button", { name: "Create Account" }).click();

  await expect(
    page.getByRole("heading", { name: "Student workspace" }),
  ).toBeVisible();
  await expect(page.getByText("Welcome, Avery Chen")).toBeVisible();

  const bookableSlots = page.getByRole("region", { name: "Bookable Slots" });
  await bookableSlots.getByRole("button").first().click();
  await expect(page.getByRole("heading", { name: "Confirm session" })).toBeVisible();
  await expect(page.getByText("Funding: First Session Promotion")).toBeVisible();
  await page.getByLabel("Optional Booking Focus").fill("Quadratic equations");
  await page.getByRole("button", { name: "Schedule session" }).click();
  await expect(page.getByRole("heading", { name: "Upcoming Booking" })).toBeVisible();
  await expect(page.getByText("Funding: first_session_promotion")).toBeVisible();

  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Student workspace" }),
  ).toBeVisible();

  await page.getByLabel("Service").selectOption("Algebra tutoring");
  await page.getByLabel("Preferred start").fill("2026-07-20T13:00");
  await page.getByLabel("Timezone").fill("America/Chicago");
  await page
    .getByLabel("Optional message")
    .fill("Please review quadratic equations.");
  await page.getByRole("button", { name: "Submit Session Request" }).click();
  await expect(
    page.getByRole("heading", { name: "Pending Session Request" }),
  ).toBeVisible();

  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const returningTutorOutboxResponse = await page.request.get(
    "/api/development/outbox",
  );
  const returningTutorOutbox = await returningTutorOutboxResponse.json();
  await page.goto(returningTutorOutbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();

  await expect(page.getByRole("heading", { name: "Students" })).toBeVisible();
  await page.getByLabel("Search Students").fill("no match");
  await expect(page.getByRole("button", { name: "Avery Chen" })).toHaveCount(0);
  await page.getByLabel("Search Students").fill("Avery");
  await page.getByRole("button", { name: "Avery Chen" }).click();
  const studentDetail = page.getByRole("dialog", { name: "Student Detail" });
  await expect(studentDetail.getByLabel("Name")).toHaveValue("Avery Chen");
  await expect(studentDetail.getByLabel("Name")).toBeEditable({ editable: false });
  await expect(studentDetail.getByLabel("Login email")).toBeEditable({
    editable: false,
  });
  await expect(studentDetail.getByText("First Session Promotion: Unavailable")).toBeVisible();
  await studentDetail.getByLabel("Credit adjustment").fill("2");
  await studentDetail
    .getByLabel("Adjustment reason")
    .fill("Two prepaid tutoring sessions");
  await studentDetail.getByRole("button", { name: "Apply credit adjustment" }).click();
  await expect(studentDetail.getByText("Session Credits: 2")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(studentDetail).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Pending Session Requests" }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("article")
      .filter({ hasText: "Algebra tutoring" })
      .getByRole("heading", { name: "Avery Chen" }),
  ).toBeVisible();
  await expect(page.getByText("Algebra tutoring")).toBeVisible();
  await expect(page.getByText("Please review quadratic equations.")).toBeVisible();
});
