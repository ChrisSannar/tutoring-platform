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
  await expect(
    page.getByRole("heading", { name: "Tutor workspace" }),
  ).toBeVisible();

  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Tutor workspace" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(
    page.getByRole("heading", { name: "Tutor sign-in" }),
  ).toBeVisible();
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

  const manualInvitation = page.getByLabel("Manual Invitation");
  await manualInvitation.getByLabel("Invitee email").fill("invitee@example.com");
  await manualInvitation.getByRole("button", { name: "Create Invitation" }).click();
  const invitationLink = await manualInvitation.getByLabel("Invitation link").inputValue();

  await page.goto(invitationLink);

  await expect(page.getByText("invitee@example.com")).toBeVisible();
});

test("Tutor corrects an active Invitation email", async ({ page }) => {
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
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
