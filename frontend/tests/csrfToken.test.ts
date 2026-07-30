import { expect, test } from "bun:test";

import { csrfTokenFromCookie } from "../src/web/csrfToken";

test("reads development and production CSRF cookies", () => {
  expect(csrfTokenFromCookie("tutoring_csrf=development")).toBe("development");
  expect(csrfTokenFromCookie("__Host-tutoring_csrf=production")).toBe("production");
  expect(
    csrfTokenFromCookie(
      "tutoring_csrf=stale; __Host-tutoring_csrf=production",
    ),
  ).toBe("production");
});
