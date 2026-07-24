import type { Page } from "@playwright/test";

export async function signInTutor(page: Page): Promise<string> {
  await page.goto("/tutor/sign-in");
  await page.getByLabel("Email address").fill("tutor@example.com");
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  const outbox = await (await page.request.get("/api/development/outbox")).json();
  await page.goto(outbox.messages.at(-1).magic_link);
  const confirmation = page.waitForResponse((response) => response.url().includes("/api/auth/magic-links/confirm"));
  await page.getByRole("button", { name: "Confirm sign-in" }).click();
  return (await (await confirmation).json()).csrf_token as string;
}
