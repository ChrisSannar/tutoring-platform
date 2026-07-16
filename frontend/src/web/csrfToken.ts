export function csrfTokenFromCookie() {
  const csrfCookie = document.cookie
    .split("; ")
    .find((cookie) => cookie.startsWith("tutoring_csrf="));
  return decodeURIComponent(csrfCookie?.split("=")[1] ?? "");
}
