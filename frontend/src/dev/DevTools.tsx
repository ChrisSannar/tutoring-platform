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

async function logOut() {
  const response = await fetch("/api/auth/logout", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfTokenFromCookie() },
  });
  if (!response.ok) throw new Error(`/api/auth/logout returned ${response.status}`);
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

const routes = [
  ["Landing page", "/"],
  ["Account sign-in", "/sign-in"],
  ["Account sign-in confirmation", "/sign-in/confirm?token=dev-token", studentMagicLink],
  ["Student workspace", "/student", async () => { await createStudent(); return "/student"; }],
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

  async function open(action: () => Promise<string>) {
    setError("");
    try {
      window.location.assign(await action());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Session setup failed");
    }
  }

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
          await open(async () => route[2] ? route[2]() : route[1]);
        }}
      >
        <option value="" disabled>Choose a route</option>
        {routes.map(([label, path]) => <option key={path} value={path}>{path.substr(0, 10)}{path.length > 10 ? "..." : ""}: {label}</option>)}
      </select>
      <fieldset className="dev-tools-session">
        <legend>Session</legend>
        <button type="button" onClick={() => void open(async () => { await createStudent(); return "/student"; })}>Log in Student</button>
        <button type="button" onClick={() => void open(async () => { await logOut(); return "/sign-in"; })}>Log out Student</button>
        <button type="button" onClick={() => void open(async () => { await authenticateTutor(); return "/tutor"; })}>Log in tutor</button>
        <button type="button" onClick={() => void open(async () => { await logOut(); return "/tutor/sign-in"; })}>Log out tutor</button>
      </fieldset>
      {error ? <p role="alert">{error}</p> : null}
    </details>
  );
}
