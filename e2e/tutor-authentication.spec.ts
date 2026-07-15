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
  await page.goto(outbox.messages[0].magic_link);

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
