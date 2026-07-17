import { useEffect, useState } from "react";

type RefundRequest = {
  id: string;
  amount_cents: number;
  currency: "USD";
  status: "pending" | "declined" | "refunded";
  student: { id: string; display_name: string };
};

export function RefundQueue({ csrfToken }: { csrfToken: string }) {
  const [requests, setRequests] = useState<RefundRequest[]>([]);

  useEffect(() => {
    void fetch("/api/tutor/refund-requests").then(async (response) => {
      if (response.ok) setRequests((await response.json()).refund_requests);
    });
  }, []);

  async function review(item: RefundRequest, action: "approve" | "decline") {
    const response = await fetch(`/api/tutor/refund-requests/${item.id}/${action}`, {
      method: "POST",
      headers: { "X-CSRF-Token": csrfToken, "Idempotency-Key": crypto.randomUUID() },
    });
    if (!response.ok) return;
    const reviewed = await response.json();
    setRequests((current) => current.map((request) => request.id === item.id ? { ...request, status: reviewed.status } : request));
  }

  const pending = requests.filter((request) => request.status === "pending");
  return <section aria-labelledby="refund-queue-heading"><h2 id="refund-queue-heading">Refund Requests</h2>{pending.length === 0 ? <p>No pending Refund Requests.</p> : pending.map((request) => <article key={request.id}><h3>{request.student.display_name}</h3><p>Full refund: {new Intl.NumberFormat("en-US", { style: "currency", currency: request.currency }).format(request.amount_cents / 100)}</p><button onClick={() => review(request, "approve")}>Approve full refund</button><button onClick={() => review(request, "decline")}>Decline and restore credit</button></article>)}</section>;
}
