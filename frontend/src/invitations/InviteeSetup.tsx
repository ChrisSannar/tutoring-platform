import { useEffect, useState } from "react";

import type { InviteeInvitation } from "./types";

function invitationToken() {
  return window.location.pathname.split("/").at(-1) ?? "";
}

export function InviteeSetup() {
  const [invitation, setInvitation] = useState<InviteeInvitation | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [verificationRequested, setVerificationRequested] = useState(false);

  useEffect(() => {
    void fetch(
      `/api/invitations/${encodeURIComponent(invitationToken())}`,
    ).then(async (response) => {
      if (!response.ok) {
        setUnavailable(true);
        return;
      }
      setInvitation(await response.json());
    });
  }, []);

  async function requestVerification() {
    if (!invitation) return;
    const response = await fetch(
      `/api/invitations/${encodeURIComponent(invitationToken())}/magic-links`,
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
