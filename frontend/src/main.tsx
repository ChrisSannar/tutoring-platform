import { FormEvent, StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

function LandingPage() {
  return (
    <main>
      <section className="hero" aria-labelledby="hero-heading">
        <p className="eyebrow">One-to-one learning</p>
        <h1 id="hero-heading">Personal tutoring, thoughtfully planned.</h1>
        <p className="intro">
          Focused sessions shaped around your goals, your questions, and the way
          you learn best.
        </p>
        <a href="mailto:tutor@example.com">Ask about tutoring</a>
      </section>
    </main>
  );
}

function TutorAuthentication() {
  const confirming = window.location.pathname === "/tutor/sign-in/confirm";
  const returning = window.location.pathname === "/tutor";
  const [screen, setScreen] = useState<
    "loading" | "sign-in" | "sent" | "confirm" | "workspace"
  >(confirming ? "confirm" : returning ? "loading" : "sign-in");
  const [email, setEmail] = useState("");
  const [csrfToken, setCsrfToken] = useState("");
  const [inviteeEmail, setInviteeEmail] = useState("");
  const [inviteeDisplayName, setInviteeDisplayName] = useState("");
  const [sharedPersonalMessage, setSharedPersonalMessage] = useState("");
  const [privateTutorNote, setPrivateTutorNote] = useState("");
  const [invitationId, setInvitationId] = useState("");
  const [invitationLink, setInvitationLink] = useState("");

  useEffect(() => {
    if (screen !== "loading") return;
    void fetch("/api/tutor/session").then((response) => {
      if (!response.ok) {
        setScreen("sign-in");
        return;
      }
      const csrfCookie = document.cookie
        .split("; ")
        .find((cookie) => cookie.startsWith("tutoring_csrf="));
      setCsrfToken(decodeURIComponent(csrfCookie?.split("=")[1] ?? ""));
      setScreen("workspace");
    });
  }, [screen]);

  async function requestLink(event: FormEvent) {
    event.preventDefault();
    await fetch("/api/auth/magic-links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    setScreen("sent");
  }

  async function confirmSignIn() {
    const token = new URLSearchParams(window.location.search).get("token");
    const response = await fetch("/api/auth/magic-links/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    if (!response.ok) return;
    const authenticated = await response.json();
    setCsrfToken(authenticated.csrf_token);
    window.history.replaceState({}, "", "/tutor");
    setScreen("workspace");
  }

  async function logOut() {
    const response = await fetch("/api/auth/logout", {
      method: "POST",
      headers: { "X-CSRF-Token": csrfToken },
    });
    if (!response.ok) return;
    window.history.replaceState({}, "", "/tutor/sign-in");
    setScreen("sign-in");
  }

  async function createInvitation(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/tutor/invitations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        email: inviteeEmail,
        display_name: inviteeDisplayName,
        shared_personal_message: sharedPersonalMessage,
        private_tutor_note: privateTutorNote,
      }),
    });
    if (!response.ok) return;
    const invitation = await response.json();
    setInvitationId(invitation.id);
  }

  async function activateInvitation() {
    const response = await fetch(
      `/api/tutor/invitations/${invitationId}/activate`,
      {
        method: "POST",
        headers: { "X-CSRF-Token": csrfToken },
      },
    );
    if (!response.ok) return;
    const invitation = await response.json();
    setInvitationLink(invitation.invitation_url);
  }

  if (screen === "sent") {
    return (
      <main><section className="hero"><h1>Check the development outbox</h1></section></main>
    );
  }
  if (screen === "loading") {
    return <main><p>Loading Tutor session…</p></main>;
  }
  if (screen === "confirm") {
    return (
      <main><section className="hero">
        <h1>Confirm Tutor sign-in</h1>
        <button onClick={confirmSignIn}>Confirm sign-in</button>
      </section></main>
    );
  }
  if (screen === "workspace") {
    return (
      <main><section className="hero">
        <h1>Tutor workspace</h1>
        {!invitationId ? (
          <form onSubmit={createInvitation}>
            <label htmlFor="invitee-email">Invitee email</label>
            <input
              id="invitee-email"
              type="email"
              value={inviteeEmail}
              onChange={(event) => setInviteeEmail(event.target.value)}
              required
            />
            <label htmlFor="invitee-display-name">Invitee display name</label>
            <input
              id="invitee-display-name"
              value={inviteeDisplayName}
              onChange={(event) => setInviteeDisplayName(event.target.value)}
              required
            />
            <label htmlFor="shared-personal-message">Shared Personal Message</label>
            <textarea
              id="shared-personal-message"
              value={sharedPersonalMessage}
              onChange={(event) => setSharedPersonalMessage(event.target.value)}
            />
            <label htmlFor="private-tutor-note">Private Tutor Note</label>
            <textarea
              id="private-tutor-note"
              value={privateTutorNote}
              onChange={(event) => setPrivateTutorNote(event.target.value)}
            />
            <button type="submit">Create Invitation</button>
          </form>
        ) : !invitationLink ? (
          <section>
            <h2>Draft Invitation for {inviteeDisplayName}</h2>
            <button onClick={activateInvitation}>Activate Invitation</button>
          </section>
        ) : (
          <section>
            <h2>Active Invitation for {inviteeDisplayName}</h2>
            <label htmlFor="invitation-link">Invitation link</label>
            <input id="invitation-link" value={invitationLink} readOnly />
          </section>
        )}
        <button onClick={logOut}>Log out</button>
      </section></main>
    );
  }
  return (
    <main><section className="hero">
      <h1>Tutor sign-in</h1>
      <form onSubmit={requestLink}>
        <label htmlFor="tutor-email">Email address</label>
        <input
          id="tutor-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <button type="submit">Email me a sign-in link</button>
      </form>
    </section></main>
  );
}

function Application() {
  if (window.location.pathname.startsWith("/tutor")) {
    return <TutorAuthentication />;
  }
  return <LandingPage />;
}

const root = document.getElementById("root");

if (!root) {
  throw new Error("Application root is missing");
}

createRoot(root).render(
  <StrictMode>
    <Application />
  </StrictMode>,
);
