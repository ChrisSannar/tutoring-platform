import { type FormEvent, useState } from "react";

export function InvitationManager({ csrfToken }: { csrfToken: string }) {
  const [inviteeEmail, setInviteeEmail] = useState("");
  const [invitationId, setInvitationId] = useState("");
  const [invitationLink, setInvitationLink] = useState("");
  const [managementMessage, setManagementMessage] = useState("");
  const [invitationRevoked, setInvitationRevoked] = useState(false);

  async function createInvitation(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/tutor/invitations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ email: inviteeEmail }),
    });
    if (!response.ok) return;
    const invitation = await response.json();
    setInviteeEmail(invitation.email);
    setInvitationId(invitation.id);
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
      { method: "POST", headers: { "X-CSRF-Token": csrfToken } },
    );
    if (!response.ok) return;
    const invitation = await response.json();
    setInvitationLink(invitation.invitation_url);
    setManagementMessage("Replacement link shown once");
  }

  async function retrieveInvitation() {
    const response = await fetch(`/api/tutor/invitations/${invitationId}/link`);
    if (!response.ok) return;
    const invitation = await response.json();
    setInvitationLink(invitation.invitation_url);
  }

  async function revokeInvitation() {
    const response = await fetch(
      `/api/tutor/invitations/${invitationId}/revoke`,
      { method: "POST", headers: { "X-CSRF-Token": csrfToken } },
    );
    if (!response.ok) return;
    setInvitationRevoked(true);
    setInvitationLink("");
  }

  if (!invitationId) {
    return (
      <form aria-label="Manual Invitation" onSubmit={createInvitation}>
        <label htmlFor="invitee-email">Invitee email</label>
        <input
          id="invitee-email"
          type="email"
          value={inviteeEmail}
          onChange={(event) => setInviteeEmail(event.target.value)}
          required
        />
        <button type="submit">Create Invitation</button>
      </form>
    );
  }
  if (invitationRevoked) {
    return <section aria-label="Manual Invitation"><h2>Revoked Invitation for {inviteeEmail}</h2></section>;
  }
  return (
    <section aria-label="Manual Invitation">
      <h2>Created Invitation for {inviteeEmail}</h2>
      <label htmlFor="invitation-link">Invitation link</label>
      <input id="invitation-link" value={invitationLink} readOnly />
      <button onClick={() => setInvitationLink("")}>Hide link</button>
      <button onClick={retrieveInvitation}>Retrieve link</button>
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
  );
}
