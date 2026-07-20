import { useState } from "react";

import { csrfTokenFromCookie } from "../web/csrfToken";

const tutorEmail = "tutor@example.com";

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

async function tutorMagicLink() {
  await json("/api/auth/magic-links", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: tutorEmail }),
  });
  const outbox = await json<{ messages: { to: string; magic_link: string }[] }>("/api/development/outbox");
  const message = [...outbox.messages].reverse().find(({ to }) => to === tutorEmail);
  if (!message) throw new Error(`Bootstrap ${tutorEmail} before using authenticated pages`);
  return message.magic_link;
}

async function authenticateTutor() {
  if ((await fetch("/api/tutor/session")).ok) return;
  const token = new URL(await tutorMagicLink(), location.origin).searchParams.get("token");
  await json("/api/auth/magic-links/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
}

const mutationHeaders = () => ({
  "Content-Type": "application/json",
  "X-CSRF-Token": csrfTokenFromCookie(),
});

async function createInvitation() {
  await authenticateTutor();
  return json<{ email: string; invitation_url: string }>("/api/tutor/invitations", {
    method: "POST",
    headers: mutationHeaders(),
    body: JSON.stringify({ email: `student-${crypto.randomUUID()}@example.com` }),
  });
}

async function createStudent() {
  const invitation = await createInvitation();
  await json(invitation.invitation_url.replace("/invite/", "/api/invitations/") + "/claim", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ display_name: "Dev Student" }),
  });
  return invitation.email;
}

async function studentMagicLink() {
  const email = await createStudent();
  await json("/api/auth/magic-links", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  await authenticateTutor();
  const queue = await json<{ login_requests: { id: string; email: string }[] }>("/api/tutor/login-requests");
  const request = queue.login_requests.find(({ email: queuedEmail }) => queuedEmail === email);
  if (!request) throw new Error("Student Login Request was not created");
  return (await json<{ magic_link: string }>(`/api/tutor/login-requests/${request.id}/magic-link`, {
    method: "POST",
    headers: mutationHeaders(),
  })).magic_link;
}

async function createCheckout() {
  await authenticateTutor();
  const settings = await json<{ tutor_timezone: string }>("/api/tutor/settings");
  const weekdayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const target = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000);
  const weekdayName = new Intl.DateTimeFormat("en-US", { weekday: "short", timeZone: settings.tutor_timezone }).format(target);
  const weekday = (weekdayNames.indexOf(weekdayName) + 6) % 7;
  await json("/api/tutor/availability-windows", {
    method: "POST",
    headers: mutationHeaders(),
    body: JSON.stringify({ weekday, start_time: "09:00", end_time: "17:00" }),
  });
  await createStudent();
  const { slots } = await json<{ slots: { start_at: string }[] }>("/api/student/bookable-slots");
  const starts = [...new Set(slots.map(({ start_at }) => start_at))];
  if (starts.length < 2) throw new Error("Development availability did not create two Bookable Slots");
  await json("/api/student/bookings", {
    method: "POST",
    headers: { ...mutationHeaders(), "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({ start_at: starts[0], focus: "Dev preview", confirmed: true }),
  });
  return json<{ checkout_session_id: string; checkout_url: string }>("/api/student/checkouts", {
    method: "POST",
    headers: { ...mutationHeaders(), "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify({ start_at: starts[1], focus: "Dev preview" }),
  });
}

const routes = [
  ["Landing page", "/"],
  ["Account sign-in", "/sign-in"],
  ["Account sign-in confirmation", "/sign-in/confirm?token=dev-token", studentMagicLink],
  ["Student workspace", "/student", async () => { await createStudent(); return "/student"; }],
  ["Checkout return", "/checkout/return?session_id=dev-session", async () => `/checkout/return?session_id=${(await createCheckout()).checkout_session_id}`],
  ["Fake checkout", "/checkout/fake/dev-session", async () => (await createCheckout()).checkout_url],
  ["Invitation", "/invite/dev-token", async () => (await createInvitation()).invitation_url],
  ["Tutor workspace", "/tutor", async () => { await authenticateTutor(); return "/tutor"; }],
  ["Tutor sign-in", "/tutor/sign-in"],
  ["Tutor sign-in confirmation", "/tutor/sign-in/confirm?token=dev-token", tutorMagicLink],
] as const;

const openKey = "dev-tools-open";
const bottomKey = "dev-tools-bottom";
const leftKey = "dev-tools-left";

export function DevTools() {
  const [bottom, setBottom] = useState(() => sessionStorage.getItem(bottomKey) === "true");
  const [left, setLeft] = useState(() => sessionStorage.getItem(leftKey) === "true");
  const [error, setError] = useState("");

  return (
    <details
      className={`dev-tools${bottom ? " dev-tools-bottom" : ""}${left ? " dev-tools-left" : ""}`}
      style={{ width: 400 }}
      open={sessionStorage.getItem(openKey) === "true"}
      onToggle={(event) => sessionStorage.setItem(openKey, String(event.currentTarget.open))}
    >
      <summary>Dev tools</summary>
      <div className="dev-tools-position-buttons" aria-label="Move dev tools">
        <button type="button" aria-label={`Move dev tools to ${bottom ? "top" : "bottom"}`} onClick={() => setBottom((value) => {
          sessionStorage.setItem(bottomKey, String(!value));
          return !value;
        })}>{bottom ? "↑" : "↓"}</button>
        <button type="button" aria-label={`Move dev tools to ${left ? "right" : "left"}`} onClick={() => setLeft((value) => {
          sessionStorage.setItem(leftKey, String(!value));
          return !value;
        })}>{left ? "→" : "←"}</button>
      </div>
      <label htmlFor="dev-route">Route</label>
      <select
        id="dev-route"
        defaultValue=""
        onChange={async (event) => {
          const selectedPath = event.currentTarget.value;
          event.currentTarget.value = "";
          const route = routes.find(([, path]) => path === selectedPath);
          if (!route) return;
          setError("");
          try {
            window.location.assign(route[2] ? await route[2]() : route[1]);
          } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Page setup failed");
          }
        }}
      >
        <option value="" disabled>Choose a route</option>
        {routes.map(([label, path]) => <option key={path} value={path}>{path.substr(0, 10)}{path.length > 10 ? "..." : ""}: {label}</option>)}
      </select>
      {error ? <p role="alert">{error}</p> : null}
    </details>
  );
}
