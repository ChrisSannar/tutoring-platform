export function csrfTokenFromCookie(cookies = document.cookie) {
  const cookieList = cookies.split("; ");
  const csrfCookie = cookieList.find((cookie) =>
    cookie.startsWith("__Host-tutoring_csrf=")
  ) ?? cookieList.find((cookie) => cookie.startsWith("tutoring_csrf="));
  return decodeURIComponent(csrfCookie?.split("=")[1] ?? "");
}
