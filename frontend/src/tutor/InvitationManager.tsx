import { type FormEvent, useState } from "react";

export function InvitationManager({ csrfToken }: { csrfToken: string }) {
  const [inviteeEmail, setInviteeEmail] = useState("");
  const [inviteeDisplayName, setInviteeDisplayName] = useState("");
  const [sharedPersonalMessage, setSharedPersonalMessage] = useState("");
  const [privateTutorNote, setPrivateTutorNote] = useState("");
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

  if (!invitationId) {
    return (
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
    );
  }
  if (invitationRevoked) {
    return <section><h2>Revoked Invitation for {inviteeDisplayName}</h2></section>;
  }
  if (!invitationLink) {
    return (
      <section>
        <h2>Draft Invitation for {inviteeDisplayName}</h2>
        <button onClick={activateInvitation}>Activate Invitation</button>
      </section>
    );
  }
  return (
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
  );
}
