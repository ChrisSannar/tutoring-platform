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

type InviteeInvitation = {
  email: string;
  display_name: string;
  shared_personal_message: string;
};

function InviteeSetup() {
  const [invitation, setInvitation] = useState<InviteeInvitation | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [verificationRequested, setVerificationRequested] = useState(false);

  useEffect(() => {
    const token = window.location.pathname.split("/").at(-1) ?? "";
    void fetch(`/api/invitations/${encodeURIComponent(token)}`).then(
      async (response) => {
        if (!response.ok) {
          setUnavailable(true);
          return;
        }
        setInvitation(await response.json());
      },
    );
  }, []);

  async function requestVerification() {
    if (!invitation) return;
    const token = window.location.pathname.split("/").at(-1) ?? "";
    const response = await fetch(
      `/api/invitations/${encodeURIComponent(token)}/magic-links`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: invitation.email }),
      },
    );
    if (response.ok) setVerificationRequested(true);
  }

  if (unavailable) {
    return (
      <main><section className="hero"><h1>Invitation unavailable</h1></section></main>
    );
  }
  if (!invitation) {
    return <main><p>Loading Invitation…</p></main>;
  }
  return (
    <main><section className="hero">
      <p className="eyebrow">Your personal Invitation</p>
      <h1>Welcome, {invitation.display_name}</h1>
      <p className="intro">{invitation.shared_personal_message}</p>
      <label htmlFor="invitee-bound-email">Bound email</label>
      <input
        id="invitee-bound-email"
        type="email"
        value={invitation.email}
        readOnly
      />
      <p>{invitation.email}</p>
      {verificationRequested ? (
        <p>Check your email to continue</p>
      ) : (
        <button onClick={requestVerification}>Email verification link</button>
      )}
    </section></main>
  );
}

type Student = {
  role: "student";
  email: string;
  display_name: string;
};

function StudentWorkspace({ initialStudent }: { initialStudent?: Student }) {
  const [student, setStudent] = useState<Student | null>(initialStudent ?? null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    if (student) return;
    void fetch("/api/student/session").then(async (response) => {
      if (!response.ok) {
        setUnavailable(true);
        return;
      }
      setStudent(await response.json());
    });
  }, [student]);

  if (unavailable) return <main><p>Student Session unavailable</p></main>;
  if (!student) return <main><p>Loading Student Session…</p></main>;
  return (
    <main><section className="hero">
      <p className="eyebrow">Your tutoring</p>
      <h1>Student workspace</h1>
      <p>Welcome, {student.display_name}</p>
    </section></main>
  );
}

function InvitationClaimConfirmation() {
  const token = new URLSearchParams(window.location.search).get("token") ?? "";
  const [invitation, setInvitation] = useState<InviteeInvitation | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [student, setStudent] = useState<Student | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    void fetch(
      `/api/invitation-claims/confirm?token=${encodeURIComponent(token)}`,
    ).then(async (response) => {
      if (!response.ok) {
        setUnavailable(true);
        return;
      }
      const confirmation = await response.json();
      setInvitation(confirmation);
      setDisplayName(confirmation.display_name);
    });
  }, [token]);

  async function confirmClaim() {
    const response = await fetch("/api/invitation-claims/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, display_name: displayName }),
    });
    if (!response.ok) {
      setUnavailable(true);
      return;
    }
    const claimed = await response.json();
    window.history.replaceState({}, "", "/student");
    setStudent(claimed);
  }

  if (student) return <StudentWorkspace initialStudent={student} />;
  if (unavailable) return <main><h1>Invitation Claim unavailable</h1></main>;
  if (!invitation) return <main><p>Loading Invitation Claim…</p></main>;
  return (
    <main><section className="hero">
      <h1>Confirm Invitation Claim</h1>
      <label htmlFor="claim-bound-email">Bound email</label>
      <input
        id="claim-bound-email"
        type="email"
        value={invitation.email}
        readOnly
      />
      <label htmlFor="claim-display-name">Display name</label>
      <input
        id="claim-display-name"
        value={displayName}
        onChange={(event) => setDisplayName(event.target.value)}
      />
      <button onClick={confirmClaim}>Confirm Invitation Claim</button>
    </section></main>
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
  const [managementMessage, setManagementMessage] = useState("");
  const [invitationRevoked, setInvitationRevoked] = useState(false);

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

  async function correctInvitationEmail() {
    const response = await fetch(`/api/tutor/invitations/${invitationId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ email: inviteeEmail }),
    });
    if (!response.ok) return;
    const invitation = await response.json();
    setInviteeEmail(invitation.email);
    setManagementMessage("Email corrected");
  }

  async function regenerateInvitation() {
    const response = await fetch(
      `/api/tutor/invitations/${invitationId}/regenerate`,
      {
        method: "POST",
        headers: { "X-CSRF-Token": csrfToken },
      },
    );
    if (!response.ok) return;
    const invitation = await response.json();
    setInvitationLink(invitation.invitation_url);
    setManagementMessage("Replacement link shown once");
  }

  async function revokeInvitation() {
    const response = await fetch(
      `/api/tutor/invitations/${invitationId}/revoke`,
      {
        method: "POST",
        headers: { "X-CSRF-Token": csrfToken },
      },
    );
    if (!response.ok) return;
    setInvitationRevoked(true);
    setInvitationLink("");
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
        ) : invitationRevoked ? (
          <section>
            <h2>Revoked Invitation for {inviteeDisplayName}</h2>
          </section>
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
            <label htmlFor="bound-email">Bound email</label>
            <input
              id="bound-email"
              type="email"
              value={inviteeEmail}
              onChange={(event) => setInviteeEmail(event.target.value)}
            />
            <button onClick={correctInvitationEmail}>Correct email</button>
            <button onClick={regenerateInvitation}>Regenerate Invitation</button>
            <button onClick={revokeInvitation}>Revoke Invitation</button>
            {managementMessage ? <p>{managementMessage}</p> : null}
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
  if (window.location.pathname === "/student/claim/confirm") {
    return <InvitationClaimConfirmation />;
  }
  if (window.location.pathname === "/student") {
    return <StudentWorkspace />;
  }
  if (window.location.pathname.startsWith("/invite/")) {
    return <InviteeSetup />;
  }
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
