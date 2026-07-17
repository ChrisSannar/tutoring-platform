import { useEffect, useState } from "react";

type Inquiry = {
  id: string;
  email: string;
  message: string;
  status: "new" | "invited";
};

type InquiryQueueProps = { csrfToken: string };

export function InquiryQueue({ csrfToken }: InquiryQueueProps) {
  const [inquiries, setInquiries] = useState<Inquiry[]>([]);

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

  return (
    <section aria-labelledby="inquiries-heading">
      <h2 id="inquiries-heading">Active Inquiries</h2>
      {inquiries.length === 0 ? <p>No active Inquiries.</p> : null}
      {inquiries.map((inquiry) => (
        <article key={inquiry.id} aria-label={inquiry.email}>
          <h3>{inquiry.email}</h3>
          <p>{inquiry.message}</p>
          <p>State: {inquiry.status === "new" ? "New" : "Invited"}</p>
          <button onClick={() => archive(inquiry)}>Archive</button>
          <button onClick={() => permanentlyDelete(inquiry)}>
            Delete permanently
          </button>
        </article>
      ))}
    </section>
  );
}
