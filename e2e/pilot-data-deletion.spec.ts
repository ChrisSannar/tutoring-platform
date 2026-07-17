import { expect, test } from "@playwright/test";

test("Tutor deliberately deletes collected Student pilot data", async ({
  page,
  playwright,
}, testInfo) => {
  const applicationOrigin = testInfo.project.use.baseURL;
  if (!applicationOrigin) {
    throw new Error("Playwright baseURL must be configured");
  }
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  let outbox = await (await page.request.get("/api/development/outbox")).json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
  const manualInvitation = page.getByLabel("Manual Invitation");
  await manualInvitation.getByLabel("Invitee email").fill("delete-me@example.com");
  await manualInvitation.getByRole("button", { name: "Create Invitation" }).click();
  const invitationLink = await manualInvitation.getByLabel("Invitation link").inputValue();

  await page.goto(invitationLink);
  await page.getByLabel("Display name").fill("Delete Me");
  await page.getByRole("button", { name: "Create Account" }).click();
  await page.getByLabel("Service").selectOption("Algebra tutoring");
  await page.getByLabel("Preferred start").fill("2026-07-20T13:00");
  await page.getByLabel("Timezone").fill("America/Chicago");
  await page.getByLabel("Optional message").fill("Delete this request message.");
  await page.getByRole("button", { name: "Submit Session Request" }).click();
  const studentCookies = await page.context().cookies();

  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  outbox = await (await page.request.get("/api/development/outbox")).json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
  await expect(
    page
      .getByRole("article")
      .filter({ hasText: "Algebra tutoring" })
      .getByRole("heading", { name: "Delete Me" }),
  ).toBeVisible();

  const sessionRequests = await (
    await page.request.get("/api/tutor/session-requests")
  ).json();
  const studentId = sessionRequests.requests.find(
    (sessionRequest: { student: { email: string } }) =>
      sessionRequest.student.email === "delete-me@example.com",
  ).student.id;
  const studentCsrf = studentCookies.find(
    (cookie) => cookie.name === "tutoring_csrf",
  )?.value;
  const studentRequest = await playwright.request.newContext({
    baseURL: applicationOrigin,
    storageState: { cookies: studentCookies, origins: [] },
  });
  const unauthorized = await studentRequest.delete(
    `/api/tutor/students/${studentId}/pilot-data`,
    {
      headers: {
        Origin: applicationOrigin,
        "X-CSRF-Token": studentCsrf ?? "",
      },
      data: { confirmation: "DELETE COLLECTED DATA" },
    },
  );
  expect(unauthorized.status()).toBe(403);
  await studentRequest.dispose();

  await page
    .getByRole("article")
    .filter({ hasText: "Delete Me" })
    .getByRole("button", { name: "Delete collected data" })
    .click();
  await expect(
    page.getByText("This permanently removes the Student's collected pilot data."),
  ).toBeVisible();
  await page.getByLabel("Type DELETE COLLECTED DATA to confirm").fill(
    "DELETE COLLECTED DATA",
  );
  await page
    .getByRole("button", { name: "Permanently delete collected data" })
    .click();

  await expect(page.getByText("Collected pilot data deleted")).toBeVisible();
  await expect(page.getByText("Delete Me")).toHaveCount(0);
  await expect(page.getByText("Delete this request message.")).toHaveCount(0);

  const deletedStudentContext = await page.context().browser()!.newContext({
    storageState: { cookies: studentCookies, origins: [] },
  });
  const deletedStudentPage = await deletedStudentContext.newPage();
  await deletedStudentPage.goto("/student");
  await expect(
    deletedStudentPage.getByText("Student Session unavailable"),
  ).toBeVisible();
  await deletedStudentContext.close();
});
