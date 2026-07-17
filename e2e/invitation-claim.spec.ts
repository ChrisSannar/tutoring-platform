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
