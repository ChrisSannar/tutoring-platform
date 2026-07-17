import { useEffect, useState } from "react";

type Inquiry = {
  id: string;
  email: string;
  message: string;
  status: "new" | "invited";
  invitation_id?: string;
};

type InquiryQueueProps = { csrfToken: string };

export function InquiryQueue({ csrfToken }: InquiryQueueProps) {
  const [inquiries, setInquiries] = useState<Inquiry[]>([]);
  const [invitationLinks, setInvitationLinks] = useState<Record<string, string>>({});

  useEffect(() => {
    void fetch("/api/tutor/inquiries")
      .then((response) => response.json())
      .then((body) => setInquiries(body.inquiries));
  }, []);

  async function archive(inquiry: Inquiry) {
    const response = await fetch(`/api/tutor/inquiries/${inquiry.id}/archive`, {
      method: "POST",
      headers: { "X-CSRF-Token": csrfToken },
    });
    if (response.ok) remove(inquiry.id);
  }

  async function permanentlyDelete(inquiry: Inquiry) {
    if (!window.confirm(`Permanently delete the Inquiry from ${inquiry.email}?`)) {
      return;
    }
    const response = await fetch(`/api/tutor/inquiries/${inquiry.id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ confirmed: true }),
    });
    if (response.ok) remove(inquiry.id);
  }

  function remove(inquiryId: string) {
    setInquiries((current) => current.filter(({ id }) => id !== inquiryId));
  }

  async function createInvitation(inquiry: Inquiry) {
    const response = await fetch(
      `/api/tutor/inquiries/${inquiry.id}/invitation`,
      { method: "POST", headers: { "X-CSRF-Token": csrfToken } },
    );
    if (!response.ok) return;
    const invitation = await response.json();
    setInquiries((current) =>
      current.map((item) =>
        item.id === inquiry.id
          ? { ...item, status: "invited", invitation_id: invitation.id }
          : item,
      ),
    );
    setInvitationLinks((current) => ({
      ...current,
      [inquiry.id]: invitation.invitation_url,
    }));
  }

  async function retrieveInvitation(inquiry: Inquiry) {
    if (!inquiry.invitation_id) return;
    const response = await fetch(
      `/api/tutor/invitations/${inquiry.invitation_id}/link`,
    );
    if (!response.ok) return;
    const invitation = await response.json();
    setInvitationLinks((current) => ({
      ...current,
      [inquiry.id]: invitation.invitation_url,
    }));
  }

  async function regenerateInvitation(inquiry: Inquiry) {
    if (!inquiry.invitation_id) return;
    const response = await fetch(
      `/api/tutor/invitations/${inquiry.invitation_id}/regenerate`,
      { method: "POST", headers: { "X-CSRF-Token": csrfToken } },
    );
    if (!response.ok) return;
    const invitation = await response.json();
    setInvitationLinks((current) => ({
      ...current,
      [inquiry.id]: invitation.invitation_url,
    }));
  }

  async function revokeInvitation(inquiry: Inquiry) {
    if (!inquiry.invitation_id) return;
    const response = await fetch(
      `/api/tutor/invitations/${inquiry.invitation_id}/revoke`,
      { method: "POST", headers: { "X-CSRF-Token": csrfToken } },
    );
    if (response.ok) {
      setInvitationLinks((current) => ({ ...current, [inquiry.id]: "" }));
    }
  }

  return (
    <section aria-labelledby="inquiries-heading">
      <h2 id="inquiries-heading">Active Inquiries</h2>
      {inquiries.length === 0 ? <p>No active Inquiries.</p> : null}
      {inquiries.map((inquiry) => (
        <article key={inquiry.id} aria-label={inquiry.email}>
          <h3>{inquiry.email}</h3>
          <p>{inquiry.message}</p>
          <p>State: {inquiry.status === "new" ? "New" : "Invited"}</p>
          {inquiry.status === "new" ? (
            <button onClick={() => createInvitation(inquiry)}>
              Create Invitation
            </button>
          ) : (
            <>
              <label htmlFor={`inquiry-invitation-${inquiry.id}`}>
                Invitation link
              </label>
              <input
                id={`inquiry-invitation-${inquiry.id}`}
                value={invitationLinks[inquiry.id] ?? ""}
                readOnly
              />
              <button onClick={() => retrieveInvitation(inquiry)}>
                Retrieve link
              </button>
              <button onClick={() => regenerateInvitation(inquiry)}>
                Regenerate Invitation
              </button>
              <button onClick={() => revokeInvitation(inquiry)}>
                Revoke Invitation
              </button>
            </>
          )}
          <button onClick={() => archive(inquiry)}>Archive</button>
          <button onClick={() => permanentlyDelete(inquiry)}>
            Delete permanently
          </button>
        </article>
      ))}
    </section>
  );
}
