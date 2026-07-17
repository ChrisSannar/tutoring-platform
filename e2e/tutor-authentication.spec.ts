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
});

test("Tutor creates and activates a personalized Invitation", async ({ page }) => {
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();

  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();

  await page.getByLabel("Invitee email").fill("Invitee@Example.COM");
  await page.getByLabel("Invitee display name").fill("Avery");
  await page
    .getByLabel("Shared Personal Message")
    .fill("I made this Invitation for you.");
  await page
    .getByLabel("Private Tutor Note")
    .fill("Needs evening availability.");
  await page.getByRole("button", { name: "Create Invitation" }).click();

  await expect(page.getByText("Draft Invitation for Avery")).toBeVisible();
  await page.getByRole("button", { name: "Activate Invitation" }).click();
  await expect(page.getByText("Active Invitation for Avery")).toBeVisible();
  await expect(page.getByLabel("Invitation link")).toHaveValue(/\/invite\//);
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

  await page.getByLabel("Invitee email").fill("invitee@example.com");
  await page.getByLabel("Invitee display name").fill("Avery");
  await page
    .getByLabel("Shared Personal Message")
    .fill("I made this Invitation for you.");
  await page
    .getByLabel("Private Tutor Note")
    .fill("Needs evening availability.");
  await page.getByRole("button", { name: "Create Invitation" }).click();
  await page.getByRole("button", { name: "Activate Invitation" }).click();
  const invitationLink = await page.getByLabel("Invitation link").inputValue();

  await page.goto(invitationLink);

  await expect(
    page.getByRole("heading", { name: "Welcome, Avery" }),
  ).toBeVisible();
  await expect(page.getByText("I made this Invitation for you.")).toBeVisible();
  await expect(page.getByText("invitee@example.com")).toBeVisible();
  await expect(page.getByText("Needs evening availability.")).toHaveCount(0);
});

test("Tutor corrects an active Invitation email", async ({ page }) => {
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outboxResponse = await page.request.get("/api/development/outbox");
  const outbox = await outboxResponse.json();
  await page.goto(outbox.messages.at(-1).magic_link);
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
  await page.getByLabel("Invitee email").fill("typo@example.com");
  await page.getByLabel("Invitee display name").fill("Avery");
  await page.getByRole("button", { name: "Create Invitation" }).click();
  await page.getByRole("button", { name: "Activate Invitation" }).click();

  await page.getByLabel("Bound email").fill("corrected@example.com");
  await page.getByRole("button", { name: "Correct email" }).click();

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
  await page.getByLabel("Invitee email").fill("invitee@example.com");
  await page.getByLabel("Invitee display name").fill("Avery");
  await page.getByRole("button", { name: "Create Invitation" }).click();
  await page.getByRole("button", { name: "Activate Invitation" }).click();
  const priorLink = await page.getByLabel("Invitation link").inputValue();

  await page.getByRole("button", { name: "Regenerate Invitation" }).click();

  await expect(page.getByLabel("Invitation link")).not.toHaveValue(priorLink);
  await expect(page.getByText("Replacement link shown once")).toBeVisible();

  await page.getByRole("button", { name: "Revoke Invitation" }).click();

  await expect(
    page.getByRole("heading", { name: "Revoked Invitation for Avery" }),
  ).toBeVisible();
  await expect(page.getByLabel("Invitation link")).toHaveCount(0);
});
