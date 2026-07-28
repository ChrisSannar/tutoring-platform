import { type FormEvent, useEffect, useState } from "react";

type InviteeInvitation = {
  email: string;
};

function invitationToken() {
  return window.location.pathname.split("/").at(-1) ?? "";
}

export function InviteeSetup() {
  const [invitation, setInvitation] = useState<InviteeInvitation | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    void fetch(`/api/invitations/${encodeURIComponent(invitationToken())}`).then(
      async (response) => {
        if (!response.ok) {
          setUnavailable(true);
          return;
        }
        setInvitation(await response.json());
      },
    );
  }, []);

  async function createAccount(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(
      `/api/invitations/${encodeURIComponent(invitationToken())}/claim`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: displayName }),
      },
    );
    if (!response.ok) {
      setUnavailable(true);
      return;
    }
    window.location.assign("/student");
  }

  if (unavailable) {
    return (
      <main className="login-authentication"><h1>Invitation unavailable</h1></main>
    );
  }
  if (!invitation) return <main className="login-authentication"><p>Loading Invitation…</p></main>;
  return (
    <main className="login-authentication">
      <p className="eyebrow">Your personal Invitation</p>
      <h1>Create your Student account</h1>
      <p>This Invitation is for <strong>{invitation.email}</strong>. Confirm that this is your email, then enter the name the Tutor should use for you.</p>
      <p>If this email is incorrect, contact the Tutor for a corrected Invitation.</p>
      <form onSubmit={createAccount}>
        <label htmlFor="invitee-bound-email">Bound email</label>
        <input
          id="invitee-bound-email"
          type="email"
          value={invitation.email}
          readOnly
        />
        <label htmlFor="invitee-display-name">Display name</label>
        <input
          id="invitee-display-name"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          maxLength={200}
          required
        />
        <button type="submit">Create Account</button>
      </form>
    </main>
  );
}
